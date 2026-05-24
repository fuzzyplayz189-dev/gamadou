"""
Moderation Commands Cog
"""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta
from src.utils.embeds import success_embed, error_embed, warning_embed, info_embed, mod_action_embed
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ModerationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def db(self):
        return self.bot.db

    async def _log_action(self, guild, data):
        await self.db.add_mod_log(data)
        config = await self.db.get_guild_config(guild.id)
        ch_id = config.get("mod_log_channel_id")
        if not ch_id: return
        ch = guild.get_channel(ch_id)
        if not ch: return
        target = guild.get_member(data["target_id"]) or data.get("target_name", str(data["target_id"]))
        mod = guild.get_member(data["moderator_id"]) or data.get("moderator_name", str(data["moderator_id"]))
        await ch.send(embed=mod_action_embed(data["action"], target, mod, data.get("reason","N/A"), data.get("duration")))

    @app_commands.command(name="ban", description="Bannt ein Mitglied")
    @app_commands.describe(member="Mitglied", reason="Grund", delete_days="Nachrichten löschen (0-7 Tage)")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Kein Grund", delete_days: int = 0):
        await interaction.response.defer()
        if member.top_role >= interaction.user.top_role:
            await interaction.followup.send(embed=error_embed("Keine Berechtigung", "Gleiche/höhere Rolle."), ephemeral=True); return
        try: await member.send(embed=error_embed(f"Gebannt von {interaction.guild.name}", f"**Grund:** {reason}"))
        except Exception: pass
        await member.ban(reason=f"{interaction.user}: {reason}", delete_message_days=min(7, max(0, delete_days)))
        await interaction.followup.send(embed=mod_action_embed("ban", member, interaction.user, reason))
        await self._log_action(interaction.guild, {"guild_id": interaction.guild.id, "action": "ban",
            "target_id": member.id, "target_name": str(member), "moderator_id": interaction.user.id,
            "moderator_name": str(interaction.user), "reason": reason, "created_at": datetime.now(timezone.utc)})

    @app_commands.command(name="unban", description="Entbannt einen User per ID")
    @app_commands.describe(user_id="User ID", reason="Grund")
    @app_commands.default_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = "Kein Grund"):
        await interaction.response.defer()
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user, reason=reason)
            await interaction.followup.send(embed=success_embed("Entbannt", f"**{user}** wurde entbannt."))
        except (discord.NotFound, ValueError):
            await interaction.followup.send(embed=error_embed("Nicht gefunden", f"User `{user_id}` nicht gefunden."), ephemeral=True)

    @app_commands.command(name="kick", description="Kickt ein Mitglied")
    @app_commands.describe(member="Mitglied", reason="Grund")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Kein Grund"):
        await interaction.response.defer()
        if member.top_role >= interaction.user.top_role:
            await interaction.followup.send(embed=error_embed("Keine Berechtigung", "Gleiche/höhere Rolle."), ephemeral=True); return
        try: await member.send(embed=error_embed(f"Gekickt von {interaction.guild.name}", f"**Grund:** {reason}"))
        except Exception: pass
        await member.kick(reason=f"{interaction.user}: {reason}")
        await interaction.followup.send(embed=mod_action_embed("kick", member, interaction.user, reason))
        await self._log_action(interaction.guild, {"guild_id": interaction.guild.id, "action": "kick",
            "target_id": member.id, "target_name": str(member), "moderator_id": interaction.user.id,
            "moderator_name": str(interaction.user), "reason": reason, "created_at": datetime.now(timezone.utc)})

    @app_commands.command(name="timeout", description="Gibt einem Mitglied einen Timeout")
    @app_commands.describe(member="Mitglied", minutes="Dauer in Minuten", reason="Grund")
    @app_commands.default_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int = 10, reason: str = "Kein Grund"):
        await interaction.response.defer()
        if member.top_role >= interaction.user.top_role:
            await interaction.followup.send(embed=error_embed("Keine Berechtigung", "Gleiche/höhere Rolle."), ephemeral=True); return
        await member.timeout(timedelta(minutes=min(40320, max(1, minutes))), reason=f"{interaction.user}: {reason}")
        await interaction.followup.send(embed=mod_action_embed("timeout", member, interaction.user, reason, duration=f"{minutes}min"))
        await self._log_action(interaction.guild, {"guild_id": interaction.guild.id, "action": "timeout",
            "target_id": member.id, "target_name": str(member), "moderator_id": interaction.user.id,
            "moderator_name": str(interaction.user), "reason": reason, "duration": f"{minutes}min", "created_at": datetime.now(timezone.utc)})

    @app_commands.command(name="untimeout", description="Hebt den Timeout auf")
    @app_commands.describe(member="Mitglied")
    @app_commands.default_permissions(moderate_members=True)
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer()
        await member.timeout(None)
        await interaction.followup.send(embed=success_embed("Timeout aufgehoben", f"Timeout von {member.mention} aufgehoben."))

    @app_commands.command(name="warn", description="Verwarnt ein Mitglied")
    @app_commands.describe(member="Mitglied", reason="Grund")
    @app_commands.default_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Kein Grund"):
        await interaction.response.defer()
        await self.db.add_warning({"guild_id": interaction.guild.id, "user_id": member.id, "user_name": str(member),
            "moderator_id": interaction.user.id, "moderator_name": str(interaction.user),
            "reason": reason, "created_at": datetime.now(timezone.utc)})
        warns = await self.db.get_warnings(interaction.guild.id, member.id)
        embed = mod_action_embed("warn", member, interaction.user, reason)
        embed.add_field(name="⚠️ Verwarnungen", value=str(len(warns)), inline=True)
        try: await member.send(embed=error_embed(f"Verwarnung in {interaction.guild.name}", f"**Grund:** {reason}\n**Gesamt:** {len(warns)}"))
        except Exception: pass
        await interaction.followup.send(embed=embed)
        await self._log_action(interaction.guild, {"guild_id": interaction.guild.id, "action": "warn",
            "target_id": member.id, "target_name": str(member), "moderator_id": interaction.user.id,
            "moderator_name": str(interaction.user), "reason": reason, "created_at": datetime.now(timezone.utc)})

    @app_commands.command(name="warnings", description="Verwarnungen eines Mitglieds")
    @app_commands.describe(member="Mitglied")
    @app_commands.default_permissions(moderate_members=True)
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)
        warns = await self.db.get_warnings(interaction.guild.id, member.id)
        if not warns:
            await interaction.followup.send(embed=success_embed("Keine Verwarnungen", f"{member.mention} hat keine Verwarnungen."), ephemeral=True); return
        embed = warning_embed(f"Verwarnungen — {member}", f"**{len(warns)}** Verwarnung(en)")
        for i, w in enumerate(warns[:10], 1):
            ts = str(w.get("created_at",""))[:10]
            embed.add_field(name=f"#{i} ({ts})", value=f"**Grund:** {w['reason']}\n**Von:** {w.get('moderator_name','N/A')}", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="clearwarnings", description="Löscht alle Verwarnungen")
    @app_commands.describe(member="Mitglied")
    @app_commands.default_permissions(administrator=True)
    async def clearwarnings(self, interaction: discord.Interaction, member: discord.Member):
        count = await self.db.clear_warnings(interaction.guild.id, member.id)
        await interaction.response.send_message(embed=success_embed("Gelöscht", f"**{count}** Verwarnung(en) von {member.mention} gelöscht."))

    @app_commands.command(name="clear", description="Löscht Nachrichten")
    @app_commands.describe(amount="Anzahl (1-100)", member="Nur von diesem Mitglied")
    @app_commands.default_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int = 10, member: discord.Member = None):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=min(100, max(1, amount)),
                                                   check=lambda m: member is None or m.author == member)
        await interaction.followup.send(embed=success_embed("Gelöscht", f"**{len(deleted)}** Nachricht(en) gelöscht."), ephemeral=True)

    @app_commands.command(name="lock", description="Sperrt einen Kanal")
    @app_commands.describe(channel="Kanal", reason="Grund")
    @app_commands.default_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction, channel: discord.TextChannel = None, reason: str = "Gesperrt"):
        ch = channel or interaction.channel
        await ch.set_permissions(interaction.guild.default_role, send_messages=False, reason=reason)
        await interaction.response.send_message(embed=success_embed("Kanal gesperrt", f"🔒 {ch.mention} gesperrt.\n**Grund:** {reason}"))

    @app_commands.command(name="unlock", description="Entsperrt einen Kanal")
    @app_commands.describe(channel="Kanal")
    @app_commands.default_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        ch = channel or interaction.channel
        await ch.set_permissions(interaction.guild.default_role, send_messages=None)
        await interaction.response.send_message(embed=success_embed("Kanal entsperrt", f"🔓 {ch.mention} entsperrt."))

    @app_commands.command(name="slowmode", description="Setzt Slowmode")
    @app_commands.describe(seconds="Sekunden (0 = deaktivieren)", channel="Kanal")
    @app_commands.default_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, seconds: int = 5, channel: discord.TextChannel = None):
        ch = channel or interaction.channel
        s = max(0, min(21600, seconds))
        await ch.edit(slowmode_delay=s)
        msg = f"Slowmode in {ch.mention}: **{s}s**" if s else f"Slowmode in {ch.mention} deaktiviert."
        await interaction.response.send_message(embed=success_embed("Slowmode", msg))

    @app_commands.command(name="role", description="Rolle hinzufügen/entfernen")
    @app_commands.describe(member="Mitglied", role="Rolle", action="Aktion")
    @app_commands.choices(action=[app_commands.Choice(name="Hinzufügen", value="add"),
                                   app_commands.Choice(name="Entfernen",  value="remove")])
    @app_commands.default_permissions(manage_roles=True)
    async def role(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role, action: str = "add"):
        await interaction.response.defer()
        if role >= interaction.user.top_role:
            await interaction.followup.send(embed=error_embed("Keine Berechtigung", "Rolle ist gleich/höher als deine."), ephemeral=True); return
        if action == "add":
            await member.add_roles(role); await interaction.followup.send(embed=success_embed("Rolle hinzugefügt", f"{role.mention} → {member.mention}"))
        else:
            await member.remove_roles(role); await interaction.followup.send(embed=success_embed("Rolle entfernt", f"{role.mention} von {member.mention}"))

    @app_commands.command(name="nickname", description="Nickname ändern/zurücksetzen")
    @app_commands.describe(member="Mitglied", nickname="Neuer Nickname (leer = zurücksetzen)")
    @app_commands.default_permissions(manage_nicknames=True)
    async def nickname(self, interaction: discord.Interaction, member: discord.Member, nickname: str = None):
        old = member.display_name
        await member.edit(nick=nickname)
        msg = f"**{old}** → **{nickname}**" if nickname else f"Nickname von {member.mention} zurückgesetzt."
        await interaction.response.send_message(embed=success_embed("Nickname", msg))

    @app_commands.command(name="modlogs", description="Mod-Logs eines Users")
    @app_commands.describe(member="Mitglied")
    @app_commands.default_permissions(manage_guild=True)
    async def modlogs(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)
        logs = await self.db.get_mod_logs(interaction.guild.id, member.id)
        if not logs:
            await interaction.followup.send(embed=success_embed("Keine Logs", f"Keine Logs für {member.mention}."), ephemeral=True); return
        embed = info_embed(f"Mod-Logs — {member}", f"{len(logs)} Eintrag/Einträge")
        for log in logs[:10]:
            ts = str(log.get("created_at",""))[:10]
            embed.add_field(name=f"🔨 {log['action'].upper()} ({ts})",
                            value=f"**Von:** {log.get('moderator_name','N/A')}\n**Grund:** {log.get('reason','N/A')}", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ModerationCommands(bot))
