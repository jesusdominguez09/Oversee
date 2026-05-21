"""
backend/config_router.py
Rutas FastAPI para leer y escribir configuración del guild.
El bot lee de la BD en cada evento, así que guardar aquí
es suficiente para que los cambios surtan efecto al instante.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import aiosqlite

router = APIRouter(prefix="/api/config", tags=["config"])

# ── MODELOS ──────────────────────────────────────────────────────

class GeneralConfig(BaseModel):
    welcome_enabled: bool = True
    welcome_channel: Optional[str] = None
    welcome_message: str = "¡Bienvenido {user} a {server}!"
    welcome_color: str = "#6366f1"
    welcome_img: Optional[str] = None
    autorole_enabled: bool = False
    autorole_user: Optional[str] = None
    autorole_bot: Optional[str] = None
    autorole_dm: Optional[str] = None
    bye_enabled: bool = False
    bye_channel: Optional[str] = None
    bye_message: Optional[str] = None
    bot_prefix: str = "!"
    bot_lang: str = "es"
    bot_dms: bool = False
    bot_quiet: bool = False


class SecurityConfig(BaseModel):
    antispam_enabled: bool = True
    spam_limit: int = 5
    spam_window: int = 3
    spam_action: str = "mute"
    spam_timeout: int = 300
    spam_dm: bool = True
    antilinks_enabled: bool = True
    links_mode: str = "malicious"
    links_allow_media: bool = True
    links_allow_trusted: bool = True
    wordfilter_enabled: bool = True
    blacklist_words: Optional[str] = None
    wordfilter_action: str = "delete"
    antiraid_enabled: bool = False
    raid_limit: int = 10
    raid_window: int = 10
    raid_action: str = "lockdown"


class LogsConfig(BaseModel):
    mod_log_enabled: bool = True
    mod_log_channel: Optional[str] = None
    msg_log_enabled: bool = True
    msg_log_channel: Optional[str] = None
    member_log_enabled: bool = True
    member_log_channel: Optional[str] = None
    server_log_enabled: bool = False
    server_log_channel: Optional[str] = None
    voice_log_enabled: bool = False
    voice_log_channel: Optional[str] = None


class TicketsConfig(BaseModel):
    ticket_category: Optional[str] = None
    ticket_transcripts: Optional[str] = None
    ticket_staff_role: Optional[str] = None
    ticket_max: int = 1
    ticket_embed_title: str = "Soporte Técnico"
    ticket_embed_body: str = "¡Hola {user}! Explica tu problema."
    ticket_color: str = "#6366f1"
    ticket_ping_staff: bool = True


# ── HELPER ───────────────────────────────────────────────────────
_db: aiosqlite.Connection = None

def set_db(conn):
    """Llamado desde main.py una vez abierta la BD."""
    global _db
    _db = conn

def _db_guard():
    if _db is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")


async def _upsert(guild_id: str, key: str, value: str):
    await _db.execute(
        "INSERT INTO guild_config_kv (guild_id, key, value) VALUES (?,?,?) "
        "ON CONFLICT(guild_id, key) DO UPDATE SET value=excluded.value",
        (guild_id, key, value)
    )
    await _db.commit()


async def _save_dict(guild_id: str, data: dict):
    for key, val in data.items():
        await _upsert(guild_id, key, str(val) if val is not None else "")


async def _get_config(guild_id: str) -> dict:
    result = {}
    async with _db.execute(
        "SELECT key, value FROM guild_config_kv WHERE guild_id=?", (guild_id,)
    ) as cur:
        async for row in cur:
            result[row[0]] = row[1]
    return result


# ── GUILD ID helper ───────────────────────────────────────────────
# En producción ven del token de sesión o query param.
# Para este proyecto simple, lo leemos del env.
import os
def _guild_id() -> str:
    gid = os.getenv("GUILD_ID", "0")
    if gid == "0":
        raise HTTPException(status_code=400, detail="GUILD_ID no configurado en .env")
    return gid


# ── ENDPOINTS ─────────────────────────────────────────────────────

@router.get("/")
async def get_all_config():
    """Retorna toda la configuración del guild."""
    _db_guard()
    return await _get_config(_guild_id())


@router.post("/general")
async def save_general(cfg: GeneralConfig):
    _db_guard()
    await _save_dict(_guild_id(), cfg.model_dump())
    return {"ok": True, "section": "general"}


@router.get("/general")
async def load_general():
    _db_guard()
    return await _get_config(_guild_id())


@router.post("/security")
async def save_security(cfg: SecurityConfig):
    _db_guard()
    await _save_dict(_guild_id(), cfg.model_dump())
    return {"ok": True, "section": "security"}


@router.get("/security")
async def load_security():
    _db_guard()
    return await _get_config(_guild_id())


@router.post("/logs")
async def save_logs(cfg: LogsConfig):
    _db_guard()
    await _save_dict(_guild_id(), cfg.model_dump())
    return {"ok": True, "section": "logs"}


@router.get("/logs")
async def load_logs():
    _db_guard()
    return await _get_config(_guild_id())


@router.post("/tickets")
async def save_tickets(cfg: TicketsConfig):
    _db_guard()
    await _save_dict(_guild_id(), cfg.model_dump())
    return {"ok": True, "section": "tickets"}


@router.get("/tickets")
async def load_tickets():
    _db_guard()
    return await _get_config(_guild_id())