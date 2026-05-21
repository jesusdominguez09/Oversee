"""
backend/security_cog.py — Oversee v2
El módulo de automod lee toda su configuración desde la BD
en cada evento. Cambiar algo en el dashboard surte efecto
en el siguiente mensaje, sin reiniciar nada.
"""

import discord
from discord.ext import commands
import time
from collections import defaultdict
import re


# ── HELPER ───────────────────────────────────────────────────────
def _bool(v: str) -> bool:
    return str(v).lower() in ("1", "true", "yes", "on")


class SecurityModule(commands.Cog, name="SecurityModule"):

    def __init__(self, bot, db, ws_broadcaster):
        self.bot = bot
        self.db = db
        self.ws_broadcaster = ws_broadcaster

        # Caché en memoria: {user_id: [timestamp, ...]}
        self.spam_cache: dict[int, list[float]] = defaultdict(list)

        # Regex base (los dominios maliciosos conocidos siempre activos)
        self._base_malicious = re.compile(
            r"(https?://)?(www\.)?(discord\.gift|grabify\.link|free-nitro\.|iplogger\.|linkvertise\.)",
            re.IGNORECASE
        )

    # ── CONFIG LOADER ─────────────────────────────────────────────
    async def _get_cfg(self, guild_id: str) -> dict:
        """Lee la config del guild desde la BD (tabla kv)."""
        cfg = {}
        if not self.db:
            return cfg
        async with self.db.execute(
            "SELECT key, value FROM guild_config_kv WHERE guild_id=?", (str(guild_id),)
        ) as cur:
            async for row in cur:
                cfg[row[0]] = row[1]
        return cfg

    # ── MAIN LISTENER ─────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        cfg = await self._get_cfg(str(message.guild.id))

        # Comprobar si el autor tiene rol inmune
        # (En este proyecto los roles inmunes se gestionan desde la BD como texto;
        # se compara con el nombre del rol)
        if await self._is_immune(message.author, cfg):
            return

        # 1. Filtro Anti-Links
        if _bool(cfg.get("antilinks_enabled", "1")):
            if await self._check_links(message, cfg):
                return

        # 2. Filtro Palabras
        if _bool(cfg.get("wordfilter_enabled", "1")):
            if await self._check_words(message, cfg):
                return

        # 3. Anti-Spam
        if _bool(cfg.get("antispam_enabled", "1")):
            await self._check_spam(message, cfg)

    # ── INMUNIDAD ─────────────────────────────────────────────────
    async def _is_immune(self, member: discord.Member, cfg: dict) -> bool:
        """Devuelve True si el miembro tiene rol inmune."""
        # Los roles administradores siempre son inmunes
        if member.guild_permissions.administrator:
            return True
        return False

    # ── ANTI-LINKS ────────────────────────────────────────────────
    async def _check_links(self, message: discord.Message, cfg: dict) -> bool:
        """Retorna True si el mensaje fue borrado."""
        mode = cfg.get("links_mode", "malicious")
        content = message.content.lower()
        blocked = False

        if mode == "malicious":
            blocked = bool(self._base_malicious.search(content))
        elif mode == "external":
            has_link = re.search(r"https?://", content, re.IGNORECASE)
            is_discord = "discord.com" in content or "discordapp.com" in content
            allow_media = _bool(cfg.get("links_allow_media", "1"))
            allow_trusted = _bool(cfg.get("links_allow_trusted", "1"))

            if has_link and not is_discord:
                is_trusted = any(d in content for d in ["youtube.com","youtu.be","twitch.tv","imgur.com","tenor.com"])
                if allow_trusted and is_trusted:
                    blocked = False
                else:
                    blocked = True
        elif mode == "all":
            blocked = bool(re.search(r"https?://", content, re.IGNORECASE))

        if blocked:
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            await message.channel.send(
                f"⛔ {message.author.mention} — enlace no permitido en este servidor.",
                delete_after=6
            )
            await self._log_threat(message.guild.id, message.author, "Link bloqueado por filtro")
            return True
        return False

    # ── WORD FILTER ───────────────────────────────────────────────
    async def _check_words(self, message: discord.Message, cfg: dict) -> bool:
        raw = cfg.get("blacklist_words", "")
        if not raw:
            return False

        words = [w.strip().lower() for w in raw.split(",") if w.strip()]
        content = message.content.lower()

        if any(w in content for w in words):
            action = cfg.get("wordfilter_action", "delete")
            try:
                await message.delete()
            except discord.Forbidden:
                pass

            if "warn" in action:
                await message.channel.send(
                    f"⚠️ {message.author.mention} — mensaje eliminado por contener palabras prohibidas.",
                    delete_after=5
                )
            if "mute" in action:
                await self._apply_timeout(message.author, 300, "Filtro de palabras")

            await self._log_threat(message.guild.id, message.author, "Filtro de palabras activado")
            return True
        return False

    # ── ANTI-SPAM ─────────────────────────────────────────────────
    async def _check_spam(self, message: discord.Message, cfg: dict):
        limit  = int(cfg.get("spam_limit",  5))
        window = int(cfg.get("spam_window", 3))
        action = cfg.get("spam_action", "mute")
        timeout_secs = int(cfg.get("spam_timeout", 300))
        notify_dm = _bool(cfg.get("spam_dm", "1"))

        uid = message.author.id
        now = time.time()
        self.spam_cache[uid].append(now)
        self.spam_cache[uid] = [t for t in self.spam_cache[uid] if now - t < window]

        if len(self.spam_cache[uid]) >= limit:
            self.spam_cache[uid].clear()

            # Purgar mensajes del spammer
            try:
                await message.channel.purge(
                    limit=limit + 2,
                    check=lambda m: m.author == message.author
                )
            except discord.Forbidden:
                pass

            # Aplicar castigo
            if action == "delete":
                pass  # ya borrado arriba
            elif action == "mute":
                await self._apply_timeout(message.author, timeout_secs, "Spam automático")
            elif action == "kick":
                try:
                    await message.author.kick(reason="Spam detectado por Oversee")
                except discord.Forbidden:
                    pass
            elif action == "ban":
                try:
                    await message.author.ban(reason="Spam masivo detectado por Oversee", delete_message_seconds=86400)
                except discord.Forbidden:
                    pass

            await message.channel.send(
                f"🛡️ {message.author.mention} — acción tomada por spam ({action}).",
                delete_after=8
            )

            if notify_dm:
                try:
                    await message.author.send(
                        f"Has sido sancionado en **{message.guild.name}** por enviar mensajes demasiado rápido.\n"
                        f"Acción aplicada: **{action}**"
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass

            await self._log_threat(message.guild.id, message.author, f"Anti-Spam ({action})")

    # ── UTILIDADES ───────────────────────────────────────────────
    async def _apply_timeout(self, member: discord.Member, seconds: int, reason: str):
        try:
            until = discord.utils.utcnow() + discord.timedelta(seconds=seconds)
            await member.timeout(until, reason=reason)
        except discord.Forbidden:
            pass

    async def _log_threat(self, guild_id, user, reason: str):
        if self.db:
            try:
                await self.db.execute(
                    "INSERT INTO security_logs (guild_id, user_id, action, reason) VALUES (?,?,?,?)",
                    (str(guild_id), str(user.id), "Automod", reason)
                )
                await self.db.commit()
            except Exception:
                pass

        await self.ws_broadcaster("security_alert", {
            "user":   str(user),
            "avatar": str(user.avatar.url) if user.avatar else None,
            "threat": reason,
        })