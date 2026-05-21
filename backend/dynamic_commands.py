"""
dynamic_commands.py — Oversee v2
Lee los comandos custom de la BD y los registra como
slash commands en Discord sin reiniciar el bot.
"""

import discord
from discord.ext import commands
from discord import app_commands


class DynamicCommands(commands.Cog, name="DynamicCommands"):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    async def reload_dynamic_commands(self, guild_id: int):
        """
        Lee custom_commands de la BD para este guild,
        registra los slash commands y los sincroniza con Discord.
        """
        if not self.db:
            return

        guild_obj = discord.Object(id=guild_id)

        # Limpiar árbol local del guild
        self.bot.tree.clear_commands(guild=guild_obj)

        async with self.db.execute(
            "SELECT trigger_name, description, reply_text, embed_title, embed_color "
            "FROM custom_commands WHERE guild_id=?",
            (str(guild_id),)
        ) as cursor:
            async for row in cursor:
                cmd_name, desc, text, title, color = row
                self._register_command(cmd_name, desc, text, title, color, guild_obj)

        try:
            await self.bot.tree.sync(guild=guild_obj)
            print(f"[OVERSEE] Comandos sincronizados — guild {guild_id}")
        except discord.HTTPException as e:
            print(f"[OVERSEE] Error sincronizando comandos: {e}")

    def _register_command(self, cmd_name, desc, text, title, color, guild_obj):
        """Crea y registra un comando slash de forma aislada."""

        def _factory(c_name, c_desc, c_text, c_title, c_color):
            @app_commands.command(name=c_name, description=c_desc or "Comando personalizado")
            async def dynamic_cmd(interaction: discord.Interaction):
                if c_title:
                    try:
                        color_int = int(c_color.replace("#", ""), 16)
                    except (ValueError, AttributeError):
                        color_int = 0x6366f1

                    embed = discord.Embed(
                        title=c_title,
                        description=c_text,
                        color=discord.Color(color_int)
                    )
                    embed.set_footer(text=interaction.guild.name if interaction.guild else "")
                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.response.send_message(c_text)

            return dynamic_cmd

        cmd = _factory(cmd_name, desc, text, title, color)
        try:
            self.bot.tree.add_command(cmd, guild=guild_obj)
        except discord.app_commands.CommandAlreadyRegistered:
            pass