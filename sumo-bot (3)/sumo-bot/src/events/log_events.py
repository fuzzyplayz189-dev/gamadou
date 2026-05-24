"""
Log Events Cog — Vollständiges Server-Logging
"""
from __future__ import annotations
import discord
from discord.ext import commands
from datetime import datetime, timezone
from src.utils.embeds import base_embed, SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR, INFO_COLOR
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class LogEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _ch(self, guild: discord.Guild, key: str):
        config = await self.bot.db.get_guild_config(guild.id)
        ch_id = config.get(key)
        return guild.get_channel(ch_id) if ch_id else None

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot: return
        ch = await self._ch(message.guild, "message_log_channel_id")
        if not ch: return
        embed = base_embed("🗑️ Nachricht gelöscht", color=ERROR_COLOR)
        embed.add_field(name="Autor", value=f"{message.author.mention} (`{message.author.id}`)", inline=True)
        embed.add_field(name="Kanal", value=message.channel.mention, inline=True)
        if message.content:
            embed.add_field(name="Inhalt", value=message.content[:1000], inline=False)
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not before.guild or before.author.bot or before.content == after.content: return
        ch = await self._ch(before.guild, "message_log_channel_id")
        if not ch: return
        embed = base_embed("✏️ Nachricht bearbeitet", color=WARNING_COLOR)
        embed.add_field(name="Autor", value=before.author.mention, inline=True)
        embed.add_field(name="Kanal", value=before.channel.mention, inline=True)
        embed.add_field(name="Vorher", value=before.content[:500] or "*leer*", inline=False)
        embed.add_field(name="Nachher", value=after.content[:500] or "*leer*", inline=False)
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        ch = await self._ch(member.guild, "member_log_channel_id")
        if not ch: return
        age = (datetime.now(timezone.utc) - member.created_at.replace(tzinfo=timezone.utc)).days
        embed = base_embed("📥 Mitglied beigetreten", color=SUCCESS_COLOR, thumbnail=str(member.display_avatar.url))
        embed.add_field(name="Mitglied", value=f"{member.mention} (`{member.id}`)", inline=True)
        embed.add_field(name="Account-Alter", value=f"{age} Tage", inline=True)
        embed.add_field(name="Mitglieder", value=str(member.guild.member_count), inline=True)
        if age < 7:
            embed.add_field(name="⚠️ Neuer Account", value="Weniger als 7 Tage alt", inline=False)
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        ch = await self._ch(member.guild, "member_log_channel_id")
        if not ch: return
        roles = [r.mention for r in member.roles if r != member.guild.default_role]
        embed = base_embed("📤 Mitglied hat verlassen", color=ERROR_COLOR, thumbnail=str(member.display_avatar.url))
        embed.add_field(name="Mitglied", value=f"{member} (`{member.id}`)", inline=True)
        embed.add_field(name="Rollen", value=", ".join(roles[:10]) or "Keine", inline=False)
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.roles == after.roles and before.nick == after.nick: return
        ch = await self._ch(before.guild, "member_log_channel_id")
        if not ch: return
        if before.nick != after.nick:
            embed = base_embed("📝 Nickname geändert", color=INFO_COLOR)
            embed.add_field(name="Mitglied", value=after.mention, inline=False)
            embed.add_field(name="Vorher", value=before.nick or "Keiner", inline=True)
            embed.add_field(name="Nachher", value=after.nick or "Keiner", inline=True)
            await ch.send(embed=embed)
        added = [r for r in after.roles if r not in before.roles]
        removed = [r for r in before.roles if r not in after.roles]
        if added or removed:
            embed = base_embed("🎭 Rollen geändert", color=INFO_COLOR)
            embed.add_field(name="Mitglied", value=after.mention, inline=False)
            if added: embed.add_field(name="✅ Hinzugefügt", value=", ".join(r.mention for r in added), inline=True)
            if removed: embed.add_field(name="❌ Entfernt", value=", ".join(r.mention for r in removed), inline=True)
            await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        ch = await self._ch(channel.guild, "mod_log_channel_id")
        if not ch: return
        embed = base_embed("📢 Kanal erstellt", color=SUCCESS_COLOR)
        embed.add_field(name="Name", value=channel.mention, inline=True)
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        ch = await self._ch(channel.guild, "mod_log_channel_id")
        if not ch: return
        embed = base_embed("🗑️ Kanal gelöscht", color=ERROR_COLOR)
        embed.add_field(name="Name", value=f"`#{channel.name}`", inline=True)
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        ch = await self._ch(member.guild, "member_log_channel_id")
        if not ch: return
        if before.channel is None and after.channel:
            embed = base_embed("🎙️ Voice beigetreten", color=SUCCESS_COLOR)
            embed.add_field(name="Mitglied", value=member.mention, inline=True)
            embed.add_field(name="Kanal", value=after.channel.mention, inline=True)
            await ch.send(embed=embed)
        elif before.channel and after.channel is None:
            embed = base_embed("🔇 Voice verlassen", color=ERROR_COLOR)
            embed.add_field(name="Mitglied", value=member.mention, inline=True)
            embed.add_field(name="Kanal", value=before.channel.mention, inline=True)
            await ch.send(embed=embed)


async def setup(bot):
    await bot.add_cog(LogEvents(bot))
