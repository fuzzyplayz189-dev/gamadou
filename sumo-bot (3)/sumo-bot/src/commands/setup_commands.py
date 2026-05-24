"""
Setup Commands Cog — /setup
"""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from src.utils.embeds import success_embed, error_embed, info_embed, base_embed, BRAND_COLOR
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SetupCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def db(self):
        return self.bot.db

    setup_group = app_commands.Group(name="setup", description="Sumo Bot einrichten")

    @setup_group.command(name="wizard", description="Zeigt den Setup-Assistenten")
    @app_commands.default_permissions(administrator=True)
    async def wizard(self, interaction: discord.Interaction):
        embed = base_embed(title="🚀 Sumo Bot Setup-Assistent", color=BRAND_COLOR,
            description=("**🎫 Ticket-System**\n`/ticket config` — Log-Kanäle, Limits\n`/ticket panel` — Panel erstellen\n\n"
                         "**🛡️ AutoMod**\n`/automod setup` — Alle Regeln einrichten\n`/automod create-keyword` — Eigener Filter\n\n"
                         "**📋 Logging**\n`/setup logging` — Log-Kanäle konfigurieren\n\n"
                         "**📂 Kategorien**\n`/setup category` — Ticket-Kategorien anpassen\n"
                         "`/setup view` — Aktuelle Konfiguration anzeigen"))
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @setup_group.command(name="logging", description="Log-Kanäle konfigurieren")
    @app_commands.describe(mod_log="Moderations-Logs", ticket_log="Ticket-Logs",
                           automod_log="AutoMod-Logs", message_log="Nachrichten-Logs", member_log="Mitglieder-Logs")
    @app_commands.default_permissions(administrator=True)
    async def logging(self, interaction: discord.Interaction, mod_log: discord.TextChannel = None,
                      ticket_log: discord.TextChannel = None, automod_log: discord.TextChannel = None,
                      message_log: discord.TextChannel = None, member_log: discord.TextChannel = None):
        await interaction.response.defer(ephemeral=True)
        updates, lines = {}, []
        if mod_log:     updates["mod_log_channel_id"] = mod_log.id;         lines.append(f"📋 Mod-Logs → {mod_log.mention}")
        if ticket_log:  updates["ticket_log_channel_id"] = ticket_log.id;   lines.append(f"🎫 Ticket-Logs → {ticket_log.mention}")
        if automod_log: updates["automod_log_channel_id"] = automod_log.id; lines.append(f"🤖 AutoMod-Logs → {automod_log.mention}")
        if message_log: updates["message_log_channel_id"] = message_log.id; lines.append(f"💬 Nachrichten-Logs → {message_log.mention}")
        if member_log:  updates["member_log_channel_id"] = member_log.id;   lines.append(f"👥 Mitglieder-Logs → {member_log.mention}")
        if updates:
            await self.db.set_guild_config(interaction.guild.id, updates)
            await interaction.followup.send(embed=success_embed("Logging konfiguriert", "\n".join(lines)), ephemeral=True)
        else:
            await interaction.followup.send(embed=info_embed("Keine Änderungen", "Keine Kanäle angegeben."), ephemeral=True)

    @setup_group.command(name="category", description="Fügt eine Ticket-Kategorie hinzu")
    @app_commands.describe(name="Kategoriename", description="Beschreibung", emoji="Emoji", staff_role="Staff-Rolle")
    @app_commands.default_permissions(manage_guild=True)
    async def add_category(self, interaction: discord.Interaction, name: str, description: str = "",
                           emoji: str = "🎫", staff_role: discord.Role = None):
        await interaction.response.defer(ephemeral=True)
        config = await self.db.get_guild_config(interaction.guild.id)
        cats = config.get("ticket_categories", [])
        if any(c["name"].lower() == name.lower() for c in cats):
            await interaction.followup.send(embed=error_embed("Vorhanden", f"Kategorie **{name}** existiert bereits."), ephemeral=True); return
        cats.append({"name": name, "description": description, "emoji": emoji,
                     "staff_roles": [staff_role.id] if staff_role else [],
                     "welcome_message": "Danke für dein Ticket! Das Team meldet sich bald."})
        await self.db.update_guild_config(interaction.guild.id, "ticket_categories", cats)
        await interaction.followup.send(embed=success_embed("Kategorie hinzugefügt", f"**{emoji} {name}** hinzugefügt."), ephemeral=True)

    @setup_group.command(name="view", description="Aktuelle Konfiguration anzeigen")
    @app_commands.default_permissions(administrator=True)
    async def view_config(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        config = await self.db.get_guild_config(interaction.guild.id)
        def ch(id_):
            if not id_: return "Nicht gesetzt"
            c = interaction.guild.get_channel(id_)
            return c.mention if c else f"`{id_}` (gelöscht)"
        embed = info_embed(f"⚙️ Konfiguration — {interaction.guild.name}", "Aktuelle Einstellungen")
        embed.add_field(name="📋 Mod-Logs",     value=ch(config.get("mod_log_channel_id")),     inline=True)
        embed.add_field(name="🎫 Ticket-Logs",  value=ch(config.get("ticket_log_channel_id")),  inline=True)
        embed.add_field(name="🤖 AutoMod-Logs", value=ch(config.get("automod_log_channel_id")), inline=True)
        embed.add_field(name="💬 Nachr.-Logs",  value=ch(config.get("message_log_channel_id")), inline=True)
        embed.add_field(name="👥 Mitgl.-Logs",  value=ch(config.get("member_log_channel_id")),  inline=True)
        cats = config.get("ticket_categories", [])
        embed.add_field(name="📂 Kategorien",
                        value="\n".join(f"{c.get('emoji','🎫')} {c['name']}" for c in cats[:10]) or "Standard (4)",
                        inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SetupCommands(bot))
