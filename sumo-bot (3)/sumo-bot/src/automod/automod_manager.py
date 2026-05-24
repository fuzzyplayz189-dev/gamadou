"""
Discord AutoMod Manager — Native Discord AutoMod via API
"""
from __future__ import annotations
import discord
from datetime import timedelta
from typing import List, Optional
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AutoModManager:
    def __init__(self, bot):
        self.bot = bot

    @property
    def db(self):
        return self.bot.db

    def _actions(self, alert_channel=None, timeout_seconds=0):
        acts = [discord.AutoModRuleAction(type=discord.AutoModRuleActionType.block_message)]
        if alert_channel:
            acts.append(discord.AutoModRuleAction(type=discord.AutoModRuleActionType.send_alert_message,
                                                   channel_id=alert_channel.id))
        if timeout_seconds > 0:
            acts.append(discord.AutoModRuleAction(type=discord.AutoModRuleActionType.timeout,
                                                   duration=timedelta(seconds=timeout_seconds)))
        return acts

    async def create_keyword_rule(self, guild, name, keywords, regex_patterns=None,
                                   exempt_roles=None, exempt_channels=None,
                                   alert_channel=None, timeout_seconds=0):
        rule = await guild.create_automod_rule(
            name=name, event_type=discord.AutoModRuleEventType.message_send,
            trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.keyword,
                                            keyword_filter=keywords, regex_patterns=regex_patterns or []),
            actions=self._actions(alert_channel, timeout_seconds),
            enabled=True, exempt_roles=exempt_roles or [], exempt_channels=exempt_channels or [],
            reason=f"Sumo Bot: '{name}'",
        )
        await self.db.save_automod_rule({"guild_id": guild.id, "rule_id": str(rule.id),
                                          "name": name, "type": "keyword", "keywords": keywords, "enabled": True})
        return rule

    async def create_mention_spam_rule(self, guild, name, mention_limit=8,
                                        alert_channel=None, timeout_seconds=60,
                                        exempt_roles=None, exempt_channels=None):
        rule = await guild.create_automod_rule(
            name=name, event_type=discord.AutoModRuleEventType.message_send,
            trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.mention_spam,
                                            mention_total_limit=mention_limit),
            actions=self._actions(alert_channel, timeout_seconds),
            enabled=True, exempt_roles=exempt_roles or [], exempt_channels=exempt_channels or [],
        )
        await self.db.save_automod_rule({"guild_id": guild.id, "rule_id": str(rule.id),
                                          "name": name, "type": "mention_spam", "enabled": True})
        return rule

    async def create_spam_rule(self, guild, name, alert_channel=None, exempt_roles=None, exempt_channels=None):
        rule = await guild.create_automod_rule(
            name=name, event_type=discord.AutoModRuleEventType.message_send,
            trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.spam),
            actions=self._actions(alert_channel), enabled=True,
            exempt_roles=exempt_roles or [], exempt_channels=exempt_channels or [],
        )
        await self.db.save_automod_rule({"guild_id": guild.id, "rule_id": str(rule.id),
                                          "name": name, "type": "spam", "enabled": True})
        return rule

    async def create_profanity_rule(self, guild, name, alert_channel=None, exempt_roles=None, exempt_channels=None):
        rule = await guild.create_automod_rule(
            name=name, event_type=discord.AutoModRuleEventType.message_send,
            trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.keyword_preset),
            actions=self._actions(alert_channel), enabled=True,
            exempt_roles=exempt_roles or [], exempt_channels=exempt_channels or [],
        )
        await self.db.save_automod_rule({"guild_id": guild.id, "rule_id": str(rule.id),
                                          "name": name, "type": "profanity", "enabled": True})
        return rule

    async def get_rules(self, guild): return await guild.fetch_automod_rules()
    async def get_rule(self, guild, rule_id):
        try: return await guild.fetch_automod_rule(rule_id)
        except discord.NotFound: return None

    async def delete_rule(self, guild, rule_id):
        rule = await self.get_rule(guild, rule_id)
        if not rule: return False
        await rule.delete(reason="Gelöscht von Sumo Bot")
        await self.db.delete_automod_rule(guild.id, str(rule_id))
        return True

    async def enable_rule(self, guild, rule_id):
        rule = await self.get_rule(guild, rule_id)
        if not rule: return False
        await rule.edit(enabled=True); return True

    async def disable_rule(self, guild, rule_id):
        rule = await self.get_rule(guild, rule_id)
        if not rule: return False
        await rule.edit(enabled=False); return True
