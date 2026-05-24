"""
Moderation Events Cog
"""
from __future__ import annotations
import discord
from discord.ext import commands
from src.utils.embeds import base_embed, ERROR_COLOR, SUCCESS_COLOR
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ModerationEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _log(self, guild, embed):
        config = await self.bot.db.get_guild_config(guild.id)
        ch_id = config.get("mod_log_channel_id")
        if ch_id:
            ch = guild.get_channel(ch_id)
            if ch:
                await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        embed = base_embed("🔨 Mitglied gebannt", color=ERROR_COLOR, thumbnail=str(user.display_avatar.url))
        embed.add_field(name="User", value=f"{user} (`{user.id}`)", inline=True)
        await self._log(guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        embed = base_embed("✅ Mitglied entbannt", color=SUCCESS_COLOR)
        embed.add_field(name="User", value=f"{user} (`{user.id}`)", inline=True)
        await self._log(guild, embed)


async def setup(bot):
    await bot.add_cog(ModerationEvents(bot))
