"""
AutoMod Events Cog
"""
from __future__ import annotations
import discord
from discord.ext import commands
from src.utils.embeds import automod_embed
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AutoModEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_automod_action(self, execution: discord.AutoModAction):
        guild = self.bot.get_guild(execution.guild_id)
        if not guild:
            return
        config = await self.bot.db.get_guild_config(guild.id)
        ch_id = config.get("automod_log_channel_id")
        if not ch_id:
            return
        ch = guild.get_channel(ch_id)
        if not ch:
            return
        try:
            rule = await guild.fetch_automod_rule(execution.rule_id)
            rule_name = rule.name
            trigger_type = rule.trigger.type.name.replace("_", " ").title()
        except Exception:
            rule_name = f"Regel #{execution.rule_id}"
            trigger_type = str(execution.rule_trigger_type).replace("_", " ").title()

        action_type = str(execution.action.type).replace("_", " ").title()
        member = guild.get_member(execution.user_id)
        embed = automod_embed(rule_name, trigger_type, action_type, member, execution.content or None)

        if execution.channel_id:
            c = guild.get_channel(execution.channel_id)
            if c:
                embed.add_field(name="📢 Kanal", value=c.mention, inline=True)
        if execution.matched_keyword:
            embed.add_field(name="🔑 Keyword", value=f"`{execution.matched_keyword}`", inline=True)
        if execution.matched_content:
            embed.add_field(name="📝 Inhalt", value=f"||{execution.matched_content[:200]}||", inline=False)
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_automod_rule_create(self, rule: discord.AutoModRule):
        logger.info(f"AutoMod-Regel erstellt: {rule.name} in Guild {rule.guild_id}")

    @commands.Cog.listener()
    async def on_automod_rule_delete(self, rule: discord.AutoModRule):
        logger.info(f"AutoMod-Regel gelöscht: {rule.name} in Guild {rule.guild_id}")


async def setup(bot):
    await bot.add_cog(AutoModEvents(bot))
