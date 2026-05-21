"""
backend/ticket_cog.py — Oversee v2
El sistema de tickets lee su configuración (título del embed,
cuerpo, color, rol de staff, máx. por usuario) desde la BD
para que el dashboard controle el comportamiento en tiempo real.
"""

import discord
from discord.ext import commands
from discord import app_commands


def _bool(v: str) -> bool:
    return str(v).lower() in ("1", "true", "yes", "on")


# ── VISTA DEL BOTÓN DE TICKET ────────────────────────────────────
class TicketView(discord.ui.View):
    def __init__(self, db, ws_broadcaster):
        super().__init__(timeout=None)
        self.db = db
        self.ws_broadcaster = ws_broadcaster

    async def _get_cfg(self, guild_id: str) -> dict:
        cfg = {}
        if not self.db:
            return cfg
        async with self.db.execute(
            "SELECT key, value FROM guild_config_kv WHERE guild_id=?", (guild_id,)
        ) as cur:
            async for row in cur:
                cfg[row[0]] = row[1]
        return cfg

    @discord.ui.button(
        label="Abrir Ticket",
        style=discord.ButtonStyle.primary,
        custom_id="oversee_open_ticket",
        emoji="🎫"
    )
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user  = interaction.user
        cfg   = await self._get_cfg(str(guild.id))

        max_tickets = int(cfg.get("ticket_max", 1))
        channel_name = f"ticket-{user.name.lower().replace(' ', '-')}"

        # Anti-abuse: comprobar ticket existente
        existing = discord.utils.get(guild.text_channels, name=channel_name)
        if existing:
            await interaction.response.send_message(
                f"Ya tienes un ticket abierto en {existing.mention}.",
                ephemeral=True
            )
            return

        # Construir permisos del canal
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
        }

        # Añadir rol de soporte si está configurado
        staff_role_name = cfg.get("ticket_staff_role", "")
        staff_role = discord.utils.find(lambda r: r.name == staff_role_name.lstrip("@"), guild.roles)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        # Crear canal (en categoría si está configurada)
        category_id = cfg.get("ticket_category")
        category = None
        if category_id and category_id.isdigit():
            category = guild.get_channel(int(category_id))

        try:
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                category=category,
                reason=f"Ticket abierto por {user}"
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "No tengo permisos para crear canales. Contacta con un administrador.",
                ephemeral=True
            )
            return

        # Guardar en BD
        if self.db:
            await self.db.execute(
                "INSERT OR IGNORE INTO tickets (ticket_id, user_id, channel_id, status) VALUES (?,?,?,?)",
                (f"TK-{ticket_channel.id}", str(user.id), str(ticket_channel.id), "open")
            )
            await self.db.commit()

        # Notificar al dashboard
        await self.ws_broadcaster("system", {
            "message": f"Ticket abierto por {user} — #{channel_name}"
        })

        # Embed interno configurable desde el dashboard
        title = cfg.get("ticket_embed_title", "Soporte Técnico")
        body  = cfg.get("ticket_embed_body",  "¡Hola {user}! Explica tu problema.")
        color_hex = cfg.get("ticket_color", "#6366f1").replace("#", "")
        try:
            color = discord.Color(int(color_hex, 16))
        except ValueError:
            color = discord.Color.blurple()

        embed = discord.Embed(
            title=title,
            description=body.replace("{user}", user.mention),
            color=color
        )
        embed.set_footer(text="Oversee — Sistema de Tickets")

        content = ""
        ping_staff = _bool(cfg.get("ticket_ping_staff", "1"))
        if ping_staff and staff_role:
            content = staff_role.mention

        close_view = CloseTicketView(self.db, self.ws_broadcaster)
        await ticket_channel.send(content=content or None, embed=embed, view=close_view)

        await interaction.response.send_message(
            f"✅ Ticket creado: {ticket_channel.mention}",
            ephemeral=True
        )


# ── VISTA PARA CERRAR TICKET ─────────────────────────────────────
class CloseTicketView(discord.ui.View):
    def __init__(self, db, ws_broadcaster):
        super().__init__(timeout=None)
        self.db = db
        self.ws_broadcaster = ws_broadcaster

    @discord.ui.button(
        label="Cerrar Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="oversee_close_ticket",
        emoji="🔒"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel

        # Marcar como cerrado en BD
        if self.db:
            await self.db.execute(
                "UPDATE tickets SET status='closed' WHERE channel_id=?",
                (str(channel.id),)
            )
            await self.db.commit()

        await self.ws_broadcaster("system", {
            "message": f"Ticket #{channel.name} cerrado por {interaction.user}"
        })

        await interaction.response.send_message("🔒 Ticket cerrado. Eliminando en 5 segundos...")
        import asyncio
        await asyncio.sleep(5)
        try:
            await channel.delete(reason=f"Ticket cerrado por {interaction.user}")
        except discord.Forbidden:
            pass


# ── EL COG ───────────────────────────────────────────────────────
class TicketModule(commands.Cog, name="TicketModule"):
    def __init__(self, bot, db, ws_broadcaster):
        self.bot = bot
        self.db = db
        self.ws_broadcaster = ws_broadcaster

    @app_commands.command(
        name="setup_tickets",
        description="[Staff] Despliega el panel de tickets en este canal"
    )
    @app_commands.default_permissions(administrator=True)
    async def setup_tickets(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Centro de Soporte",
            description=(
                "Pulsa el botón de abajo para abrir un canal privado con nuestro equipo.\n\n"
                "**Reglas:**\n"
                "— Describe tu problema con detalle\n"
                "— Un miembro del staff te atenderá\n"
                "— No abras tickets innecesarios"
            ),
            color=discord.Color.from_str("#6366f1")
        )
        embed.set_footer(text="Oversee — Sistema de Soporte")

        view = TicketView(self.db, self.ws_broadcaster)
        await interaction.response.send_message("Desplegando panel...", ephemeral=True)
        await interaction.channel.send(embed=embed, view=view)