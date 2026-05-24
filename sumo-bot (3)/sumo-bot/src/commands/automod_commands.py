"""
AutoMod Commands Cog — /automod Slash-Commands
"""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from src.automod.automod_manager import AutoModManager
from src.utils.embeds import success_embed, error_embed, info_embed, EMOJI
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AutoModCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.manager = AutoModManager(bot)

    automod_group = app_commands.Group(name="automod", description="Discord AutoMod verwalten")

    @automod_group.command(name="list", description="Zeigt alle AutoMod-Regeln")
    @app_commands.default_permissions(manage_guild=True)
    async def list_rules(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        rules = await self.manager.get_rules(interaction.guild)
        if not rules:
            await interaction.followup.send(embed=info_embed("Keine Regeln", "Keine AutoMod-Regeln auf diesem Server."), ephemeral=True); return
        embed = info_embed(f"{EMOJI['automod']} AutoMod-Regeln", f"**{len(rules)}** Regel(n)")
        for r in rules:
            trigger = r.trigger.type.name.replace("_"," ").title()
            actions = ", ".join(a.type.name.replace("_"," ").title() for a in r.actions)
            embed.add_field(name=f"{'🟢' if r.enabled else '🔴'} {r.name}",
                            value=f"**ID:** `{r.id}`\n**Trigger:** {trigger}\n**Aktionen:** {actions}", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @automod_group.command(name="create-keyword", description="Erstellt einen Keyword-Filter")
    @app_commands.describe(name="Regelname", keywords="Kommagetrennte Keywords (z.B. spam,scam)",
                           alert_channel="Alert-Kanal", timeout_duration="Timeout in Sekunden (0 = kein Timeout)")
    @app_commands.default_permissions(manage_guild=True)
    async def create_keyword(self, interaction: discord.Interaction, name: str, keywords: str,
                              alert_channel: discord.TextChannel = None, timeout_duration: int = 0):
        await interaction.response.defer(ephemeral=True)
        kw = [k.strip() for k in keywords.split(",") if k.strip()]
        if not kw:
            await interaction.followup.send(embed=error_embed("Keine Keywords", "Mindestens ein Keyword angeben."), ephemeral=True); return
        try:
            rule = await self.manager.create_keyword_rule(interaction.guild, name, kw,
                                                           alert_channel=alert_channel, timeout_seconds=timeout_duration)
            await interaction.followup.send(embed=success_embed("Keyword-Regel erstellt",
                f"**Regel:** {rule.name}\n**ID:** `{rule.id}`\n**Keywords:** {len(kw)}\n"
                f"**Alert:** {alert_channel.mention if alert_channel else 'Kein'}"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Fehler", str(e)[:500]), ephemeral=True)

    @automod_group.command(name="create-mention-spam", description="Mention-Spam Schutz")
    @app_commands.describe(name="Regelname", max_mentions="Max. Erwähnungen", alert_channel="Alert-Kanal", timeout_duration="Timeout in Sekunden")
    @app_commands.default_permissions(manage_guild=True)
    async def create_mention_spam(self, interaction: discord.Interaction, name: str = "Sumo | Mention Spam",
                                   max_mentions: int = 8, alert_channel: discord.TextChannel = None, timeout_duration: int = 60):
        await interaction.response.defer(ephemeral=True)
        try:
            rule = await self.manager.create_mention_spam_rule(interaction.guild, name, max_mentions, alert_channel, timeout_duration)
            await interaction.followup.send(embed=success_embed("Mention-Spam Regel erstellt",
                f"**Regel:** {rule.name}\n**ID:** `{rule.id}`\n**Max. Erwähnungen:** {max_mentions}"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Fehler", str(e)[:500]), ephemeral=True)

    @automod_group.command(name="create-spam", description="Spam-Filter aktivieren")
    @app_commands.describe(name="Regelname", alert_channel="Alert-Kanal")
    @app_commands.default_permissions(manage_guild=True)
    async def create_spam(self, interaction: discord.Interaction, name: str = "Sumo | Spam Schutz", alert_channel: discord.TextChannel = None):
        await interaction.response.defer(ephemeral=True)
        try:
            rule = await self.manager.create_spam_rule(interaction.guild, name, alert_channel)
            await interaction.followup.send(embed=success_embed("Spam-Regel erstellt", f"**ID:** `{rule.id}`"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Fehler", str(e)[:500]), ephemeral=True)

    @automod_group.command(name="create-profanity", description="Schimpfwort-Filter aktivieren")
    @app_commands.describe(name="Regelname", alert_channel="Alert-Kanal")
    @app_commands.default_permissions(manage_guild=True)
    async def create_profanity(self, interaction: discord.Interaction, name: str = "Sumo | Profanity Filter", alert_channel: discord.TextChannel = None):
        await interaction.response.defer(ephemeral=True)
        try:
            rule = await self.manager.create_profanity_rule(interaction.guild, name, alert_channel)
            await interaction.followup.send(embed=success_embed("Profanity-Regel erstellt", f"**ID:** `{rule.id}`"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Fehler", str(e)[:500]), ephemeral=True)

    @automod_group.command(name="delete", description="Löscht eine AutoMod-Regel per ID")
    @app_commands.describe(rule_id="Regel-ID")
    @app_commands.default_permissions(manage_guild=True)
    async def delete_rule(self, interaction: discord.Interaction, rule_id: str):
        await interaction.response.defer(ephemeral=True)
        try:
            ok = await self.manager.delete_rule(interaction.guild, int(rule_id))
            if ok:
                await interaction.followup.send(embed=success_embed("Gelöscht", f"Regel `{rule_id}` gelöscht."), ephemeral=True)
            else:
                await interaction.followup.send(embed=error_embed("Nicht gefunden", f"Regel `{rule_id}` nicht gefunden."), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Fehler", str(e)[:500]), ephemeral=True)

    @automod_group.command(name="enable", description="Aktiviert eine AutoMod-Regel")
    @app_commands.describe(rule_id="Regel-ID")
    @app_commands.default_permissions(manage_guild=True)
    async def enable_rule(self, interaction: discord.Interaction, rule_id: str):
        await interaction.response.defer(ephemeral=True)
        ok = await self.manager.enable_rule(interaction.guild, int(rule_id))
        msg = success_embed("Aktiviert", f"Regel `{rule_id}` aktiv.") if ok else error_embed("Fehler", "Nicht gefunden.")
        await interaction.followup.send(embed=msg, ephemeral=True)

    @automod_group.command(name="disable", description="Deaktiviert eine AutoMod-Regel")
    @app_commands.describe(rule_id="Regel-ID")
    @app_commands.default_permissions(manage_guild=True)
    async def disable_rule(self, interaction: discord.Interaction, rule_id: str):
        await interaction.response.defer(ephemeral=True)
        ok = await self.manager.disable_rule(interaction.guild, int(rule_id))
        msg = success_embed("Deaktiviert", f"Regel `{rule_id}` deaktiviert.") if ok else error_embed("Fehler", "Nicht gefunden.")
        await interaction.followup.send(embed=msg, ephemeral=True)

    @automod_group.command(name="setup", description="Richtet alle empfohlenen AutoMod-Regeln ein")
    @app_commands.describe(alert_channel="Alert-Kanal für alle Regeln")
    @app_commands.default_permissions(administrator=True)
    async def quick_setup(self, interaction: discord.Interaction, alert_channel: discord.TextChannel = None):
        await interaction.response.defer(ephemeral=True)
        created, failed = [], []
        for label, coro in [
            ("Mention Spam",    self.manager.create_mention_spam_rule(interaction.guild, "Sumo | Mention Spam", alert_channel=alert_channel, timeout_seconds=60)),
            ("Spam Schutz",     self.manager.create_spam_rule(interaction.guild, "Sumo | Spam Schutz", alert_channel=alert_channel)),
            ("Profanity Filter", self.manager.create_profanity_rule(interaction.guild, "Sumo | Profanity Filter", alert_channel=alert_channel)),
        ]:
            try:
                await coro; created.append(label)
            except Exception as e:
                failed.append(f"{label}: {str(e)[:60]}")
        embed = success_embed("AutoMod Quick-Setup abgeschlossen",
            "\n".join(f"✅ {r}" for r in created) +
            (f"\n\n**Fehlgeschlagen:**\n" + "\n".join(f"❌ {r}" for r in failed) if failed else ""))
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(AutoModCommands(bot))
