"""
setup_cog.py — Comandos de configuración para Oversee
Implementa: /setup_ticket, /setup_verificar, etc.
"""

import discord
from discord.ext import commands
from discord import app_commands


class SetupCommands(commands.Cog, name="SetupCommands"):
    
    def __init__(self, bot, db, ws_broadcaster):
        self.bot = bot
        self.db = db
        self.ws_broadcaster = ws_broadcaster
    
    async def _save_config(self, guild_id: str, key: str, value: str):
        """Guarda o actualiza una configuración en la BD."""
        if not self.db:
            return
        await self.db.execute(
            "INSERT OR REPLACE INTO guild_config_kv (guild_id, key, value) VALUES (?, ?, ?)",
            (guild_id, key, value)
        )
        await self.db.commit()
    
    @app_commands.command(
        name="setup_ticket",
        description="Configura el sistema de tickets del servidor"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ticket(
        self,
        interaction: discord.Interaction,
        category: discord.CategoryChannel = None,
        staff_role: discord.Role = None,
        max_tickets: int = 1
    ):
        """Configura tickets: categoría, rol de staff, máximo por usuario."""
        guild_id = str(interaction.guild.id)
        
        # Guardar configuración
        if category:
            await self._save_config(guild_id, "ticket_category", str(category.id))
        if staff_role:
            await self._save_config(guild_id, "ticket_staff_role", staff_role.name)
        
        await self._save_config(guild_id, "ticket_max", str(max_tickets))
        
        # Valores por defecto si no existen
        await self._save_config(guild_id, "ticket_embed_title", "Soporte Técnico")
        await self._save_config(guild_id, "ticket_embed_body", "¡Hola {user}! Explica tu problema.")
        await self._save_config(guild_id, "ticket_color", "#6366f1")
        await self._save_config(guild_id, "ticket_ping_staff", "1")
        
        embed = discord.Embed(
            title="✅ Tickets Configurados",
            description="Sistema de tickets activado correctamente",
            color=discord.Color.green()
        )
        if category:
            embed.add_field(name="Categoría", value=category.mention, inline=False)
        if staff_role:
            embed.add_field(name="Rol de Staff", value=staff_role.mention, inline=False)
        embed.add_field(name="Máx. Tickets/Usuario", value=str(max_tickets), inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Notificar dashboard
        await self.ws_broadcaster("system", {
            "message": f"Tickets configurados en {interaction.guild.name}"
        })
    
    @app_commands.command(
        name="setup_verificar",
        description="Configura el sistema de verificación del servidor"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_verificar(
        self,
        interaction: discord.Interaction,
        verification_role: discord.Role,
        verification_channel: discord.TextChannel = None
    ):
        """Configura verificación: rol asignado, canal donde se verifica."""
        guild_id = str(interaction.guild.id)
        
        # Guardar configuración
        await self._save_config(guild_id, "verification_role", verification_role.name)
        if verification_channel:
            await self._save_config(guild_id, "verification_channel", str(verification_channel.id))
        
        # Valores por defecto
        await self._save_config(guild_id, "verification_enabled", "1")
        
        embed = discord.Embed(
            title="✅ Verificación Configurada",
            description="Sistema de verificación activado correctamente",
            color=discord.Color.green()
        )
        embed.add_field(name="Rol de Verificado", value=verification_role.mention, inline=False)
        if verification_channel:
            embed.add_field(name="Canal de Verificación", value=verification_channel.mention, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Notificar dashboard
        await self.ws_broadcaster("system", {
            "message": f"Verificación configurada en {interaction.guild.name}"
        })


async def setup(bot):
    """Función para cargar el módulo cuando se requiera."""
    # Se cargar en main.py directamente
    pass
