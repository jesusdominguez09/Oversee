"""
main.py — Oversee Core v2
Servidor FastAPI + Bot Discord en un solo proceso asyncio.
"""

import asyncio
import os
import aiosqlite
import uvicorn

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

import discord
from discord.ext import commands
from dotenv import load_dotenv

from backend.security_cog import SecurityModule
from backend.ticket_cog import TicketModule
from backend.dynamic_commands import DynamicCommands
from backend.setup_cog import SetupCommands

# ── INIT & GLOBALES ──────────────────────────────────────────────
load_dotenv()

ws_clients: list[WebSocket] = []
db_pool: Optional[aiosqlite.Connection] = None

app = FastAPI(title="Oversee API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir el frontend
app.mount("/css", StaticFiles(directory="web/css"), name="css")
app.mount("/js",  StaticFiles(directory="web/js"),  name="js")

# ── FUNCIONES DEL BOT ────────────────────────────────────────────
# 1. Definimos la función PRIMERO
async def _get_prefix(bot, message):
    """Lee el prefijo. Por ahora estático, preparado para DB."""
    return os.getenv("BOT_PREFIX", "!")

# 2. LUEGO inicializamos el bot usando la función ya existente
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix=_get_prefix, intents=intents, help_command=None)

# ── WEBSOCKET BROADCAST ──────────────────────────────────────────
async def broadcast(event_type: str, data: dict):
    dead = []
    for client in ws_clients:
        try:
            await client.send_json({"type": event_type, "data": data})
        except Exception:
            dead.append(client)
    for d in dead:
        try: ws_clients.remove(d)
        except ValueError: pass


# ── REST ENDPOINTS ───────────────────────────────────────────────
@app.get("/")
async def serve_dashboard():
    return FileResponse("web/index.html")

@app.get("/api/stats")
async def get_stats():
    guild_id = int(os.getenv("GUILD_ID", 0))
    guild = bot.get_guild(guild_id)

    if not guild:
        return {
            "guild_id": str(guild_id), "bot_ping": 0, "total_members": 0,
            "online_members": 0, "active_tickets": 0, "threats_blocked": 0
        }

    threats = 0
    if db_pool:
        async with db_pool.execute(
            "SELECT COUNT(*) FROM security_logs WHERE guild_id=? AND date(timestamp)=date('now')",
            (str(guild_id),)
        ) as cur:
            row = await cur.fetchone()
            threats = row[0] if row else 0

    open_tickets = 0
    if db_pool:
        async with db_pool.execute("SELECT COUNT(*) FROM tickets WHERE status='open'") as cur:
            row = await cur.fetchone()
            open_tickets = row[0] if row else 0

    return {
        "guild_id":       str(guild.id),
        "bot_ping":       round(bot.latency * 1000),
        "total_members":  guild.member_count,
        "online_members": sum(1 for m in guild.members if str(m.status) != "offline"),
        "active_tickets": open_tickets,
        "threats_blocked": threats,
    }


# ── COMMANDS API ─────────────────────────────────────────────────
class CommandPayload(BaseModel):
    name: str
    description: str = "Comando personalizado"
    color: str = "#6366f1"
    title: Optional[str] = None
    text: str

@app.get("/api/commands")
async def list_commands():
    if not db_pool: return []
    guild_id = os.getenv("GUILD_ID", "0")
    cmds = []
    async with db_pool.execute(
        "SELECT id, trigger_name, description, embed_title, embed_color FROM custom_commands WHERE guild_id=?",
        (guild_id,)
    ) as cur:
        async for row in cur:
            cmds.append({
                "id": row[0], "trigger_name": row[1],
                "description": row[2], "embed_title": row[3], "embed_color": row[4]
            })
    return cmds

@app.post("/api/commands")
async def create_command(payload: CommandPayload):
    if not db_pool: raise HTTPException(status_code=503, detail="DB no disponible")
    guild_id = os.getenv("GUILD_ID", "0")
    name = payload.name.replace("/", "").strip().lower()

    if not name: raise HTTPException(status_code=400, detail="Nombre inválido")

    await db_pool.execute("DELETE FROM custom_commands WHERE guild_id=? AND trigger_name=?", (guild_id, name))
    await db_pool.execute(
        "INSERT INTO custom_commands (guild_id, trigger_name, description, reply_text, embed_title, embed_color) VALUES (?,?,?,?,?,?)",
        (guild_id, name, payload.description, payload.text, payload.title, payload.color)
    )
    await db_pool.commit()

    dynamic_cog: DynamicCommands = bot.get_cog("DynamicCommands")
    if dynamic_cog:
        await dynamic_cog.reload_dynamic_commands(int(guild_id))

    await broadcast("system", {"message": f"Comando /{name} creado desde el dashboard"})
    return {"ok": True, "message": f"/{name} inyectado en Discord"}

@app.delete("/api/commands/{cmd_id}")
async def delete_command(cmd_id: int):
    if not db_pool: raise HTTPException(status_code=503, detail="DB no disponible")
    guild_id = os.getenv("GUILD_ID", "0")
    await db_pool.execute("DELETE FROM custom_commands WHERE id=? AND guild_id=?", (cmd_id, guild_id))
    await db_pool.commit()

    dynamic_cog: DynamicCommands = bot.get_cog("DynamicCommands")
    if dynamic_cog:
        await dynamic_cog.reload_dynamic_commands(int(guild_id))
    return {"ok": True}


# ── CONFIG ENDPOINTS ─────────────────────────────────────────────
@app.post("/api/config/{section}")
async def save_config(section: str, payload: dict):
    """Endpoint para guardar configuración de cualquier sección en la BD"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")
    
    guild_id = os.getenv("GUILD_ID", "0")
    
    # Guardar cada clave de configuración en la BD
    for key, value in payload.items():
        try:
            await db_pool.execute(
                "INSERT OR REPLACE INTO guild_config_kv (guild_id, key, value) VALUES (?, ?, ?)",
                (guild_id, f"{section}_{key}", str(value))
            )
        except Exception as e:
            print(f"Error guardando config: {e}")
    
    await db_pool.commit()
    await broadcast("config_update", {"section": section, "guild_id": guild_id})
    return {"ok": True, "section": section}


# ── WEBSOCKET ────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_clients.append(websocket)
    try:
        while True: await websocket.receive_text()
    except Exception:
        try: ws_clients.remove(websocket)
        except ValueError: pass


# ── BOT EVENTS ───────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"🛡️  Oversee online como {bot.user}")
    
    # Cargar módulos
    await bot.add_cog(SecurityModule(bot, db_pool, broadcast))
    await bot.add_cog(TicketModule(bot, db_pool, broadcast))
    await bot.add_cog(SetupCommands(bot, db_pool, broadcast))
    await bot.add_cog(DynamicCommands(bot, db_pool))

    guild_id = int(os.getenv("GUILD_ID", 0))
    if guild_id:
        dyn: DynamicCommands = bot.get_cog("DynamicCommands")
        if dyn:
            await dyn.reload_dynamic_commands(guild_id)

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # Ignorar mensajes largos para no saturar el panel web
    await broadcast("chat_activity", {
        "user":    message.author.name,
        "channel": message.channel.name if hasattr(message.channel, 'name') else "DM",
        "content": message.content[:80],
    })
    await bot.process_commands(message)


# ── STARTUP ──────────────────────────────────────────────────────
async def init_db():
    global db_pool
    db_pool = await aiosqlite.connect("database/oversee.db")
    
    # Asegurar que las tablas existen
    with open("database/schema.sql", "r", encoding="utf-8") as f:
        await db_pool.executescript(f.read())
    await db_pool.commit()

async def main():
    await init_db()
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    await asyncio.gather(
        server.serve(),
        bot.start(os.getenv("DISCORD_TOKEN"))
    )

if __name__ == "__main__":
    asyncio.run(main())