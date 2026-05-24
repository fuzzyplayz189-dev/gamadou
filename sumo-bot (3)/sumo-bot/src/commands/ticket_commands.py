"""
Ticket Commands Cog — /ticket Slash-Commands
"""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from src.tickets.ticket_manager import TicketManager
from src.tickets.panel_manager import PanelManager
from src.utils.embeds import success_embed, error_embed, info_embed, stats_embed, BRAND_COLOR
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TicketCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def db(self):
        return self.bot.db

    ticket_group = app_commands.Group(name="ticket", description="Ticket-System Verwaltung")

    @ticket_group.command(name="panel", description="Erstellt ein Ticket-Panel in diesem Kanal")
    @app_commands.describe(title="Panel-Titel", description="Panel-Beschreibung", style="buttons oder select")
    @app_commands.choices(style=[app_commands.Choice(name="Buttons", value="buttons"),
                                  app_commands.Choice(name="Select-Menü", value="select")])
    @app_commands.default_permissions(manage_guild=True)
    async def create_panel(self, interaction: discord.Interaction, title: str = "📋 Support Center",
                           description: str = "Öffne ein Ticket für Fragen und Probleme.", style: str = "buttons"):
        await interaction.response.defer(ephemeral=True)
        config = await self.db.get_guild_config(interaction.guild.id)
        categories = config.get("ticket_categories", [])
        if not categories:
            from src.config.settings import DEFAULT_TICKET_CONFIG
            categories = DEFAULT_TICKET_CONFIG.default_categories
        msg = await PanelManager(self.bot).create_panel(interaction.channel, title, description, categories, style)
        await interaction.followup.send(embed=success_embed("Panel erstellt", f"[Zur Nachricht]({msg.jump_url})"), ephemeral=True)

    @ticket_group.command(name="close", description="Schließt das aktuelle Ticket")
    @app_commands.describe(reason="Grund für das Schließen")
    async def close(self, interaction: discord.Interaction, reason: str = "Kein Grund"):
        await interaction.response.defer()
        if not await TicketManager(self.bot).close_ticket(interaction.channel, interaction.user, reason):
            await interaction.followup.send(embed=error_embed("Kein Ticket", "Dieser Kanal ist kein offenes Ticket."), ephemeral=True)

    @ticket_group.command(name="claim", description="Übernimmt dieses Ticket")
    async def claim(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not await TicketManager(self.bot).claim_ticket(interaction.channel, interaction.user):
            await interaction.followup.send(embed=error_embed("Fehler", "Konnte nicht übernommen werden."), ephemeral=True)

    @ticket_group.command(name="add", description="Fügt einen User hinzu")
    @app_commands.describe(member="Mitglied hinzufügen")
    async def add_user(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)
        if not await self.db.get_ticket_by_channel(interaction.channel.id):
            await interaction.followup.send(embed=error_embed("Kein Ticket", "Kein Ticket-Kanal."), ephemeral=True); return
        await TicketManager(self.bot).add_user(interaction.channel, member)
        await interaction.followup.send(embed=success_embed("Hinzugefügt", f"{member.mention} hinzugefügt."), ephemeral=True)

    @ticket_group.command(name="remove", description="Entfernt einen User")
    @app_commands.describe(member="Mitglied entfernen")
    async def remove_user(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)
        if not await self.db.get_ticket_by_channel(interaction.channel.id):
            await interaction.followup.send(embed=error_embed("Kein Ticket", "Kein Ticket-Kanal."), ephemeral=True); return
        await TicketManager(self.bot).remove_user(interaction.channel, member)
        await interaction.followup.send(embed=success_embed("Entfernt", f"{member.mention} entfernt."), ephemeral=True)

    @ticket_group.command(name="rename", description="Benennt den Ticket-Kanal um")
    @app_commands.describe(name="Neuer Name")
    async def rename(self, interaction: discord.Interaction, name: str):
        if not await self.db.get_ticket_by_channel(interaction.channel.id):
            await interaction.response.send_message(embed=error_embed("Kein Ticket", "Kein Ticket-Kanal."), ephemeral=True); return
        await interaction.channel.edit(name=name[:100])
        await interaction.response.send_message(embed=success_embed("Umbenannt", f"Kanal: `{name}`"))

    @ticket_group.command(name="priority", description="Ändert die Priorität")
    @app_commands.choices(priority=[
        app_commands.Choice(name="🟢 Niedrig",  value="low"),
        app_commands.Choice(name="🟡 Mittel",   value="medium"),
        app_commands.Choice(name="🔴 Hoch",     value="high"),
        app_commands.Choice(name="🚨 Kritisch", value="critical"),
    ])
    async def set_priority(self, interaction: discord.Interaction, priority: str):
        if await TicketManager(self.bot).set_priority(interaction.channel, priority):
            await interaction.response.send_message(embed=success_embed("Priorität", f"**{priority.capitalize()}**"))
        else:
            await interaction.response.send_message(embed=error_embed("Fehler", "Kein Ticket."), ephemeral=True)

    @ticket_group.command(name="transcript", description="Erstellt ein Transcript")
    @app_commands.choices(format=[app_commands.Choice(name="HTML", value="html"),
                                   app_commands.Choice(name="JSON", value="json"),
                                   app_commands.Choice(name="TXT",  value="txt")])
    async def transcript(self, interaction: discord.Interaction, format: str = "html"):
        await interaction.response.defer(ephemeral=True)
        from src.transcripts.transcript_generator import TranscriptGenerator
        path = await TranscriptGenerator(self.bot).generate(interaction.channel, interaction.user, fmt=format)
        if path:
            await interaction.followup.send(embed=success_embed("Transcript erstellt", ""),
                                            file=discord.File(path), ephemeral=True)
        else:
            await interaction.followup.send(embed=error_embed("Fehler", "Kein Ticket-Kanal."), ephemeral=True)

    @ticket_group.command(name="stats", description="Ticket-Statistiken")
    @app_commands.default_permissions(manage_guild=True)
    async def ticket_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        raw = await self.db.get_ticket_stats(interaction.guild.id)
        avg_h = round((raw.get("avg_close_time") or 0) / 3600, 1)
        embed = stats_embed("📊 Ticket-Statistiken", {"📬 Gesamt": raw.get("total",0),
            "🟢 Offen": raw.get("open",0), "🔒 Geschlossen": raw.get("closed",0),
            "⏱️ Ø Bearbeitungszeit": f"{avg_h}h"}, color=BRAND_COLOR)
        await interaction.followup.send(embed=embed)

    @ticket_group.command(name="history", description="Ticket-Historie eines Users")
    @app_commands.describe(member="Mitglied")
    @app_commands.default_permissions(manage_guild=True)
    async def history(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)
        tickets = [t for t in await self.db.get_guild_tickets(interaction.guild.id)
                   if t.get("creator_id") == member.id][:10]
        if not tickets:
            await interaction.followup.send(embed=info_embed("Keine Historie", f"{member.mention} hat keine Tickets."), ephemeral=True); return
        embed = info_embed(f"Ticket-Historie — {member}", f"{len(tickets)} Tickets")
        for t in tickets:
            emoji = "🟢" if t["status"] == "open" else "🔒"
            embed.add_field(name=f"{emoji} #{str(t['ticket_id']).zfill(4)} — {t.get('category','N/A')}",
                            value=f"**Betreff:** {t.get('subject','N/A')}\n**Priorität:** {t.get('priority','N/A').capitalize()}", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @ticket_group.command(name="config", description="Ticket-Einstellungen")
    @app_commands.describe(log_channel="Log-Kanal", ticket_category="Ticket-Kategorie", max_per_user="Max. Tickets pro User")
    @app_commands.default_permissions(administrator=True)
    async def config(self, interaction: discord.Interaction, log_channel: discord.TextChannel = None,
                     ticket_category: discord.CategoryChannel = None, max_per_user: int = None):
        await interaction.response.defer(ephemeral=True)
        updates = {}
        if log_channel: updates["ticket_log_channel_id"] = log_channel.id
        if ticket_category: updates["ticket_config.ticket_category_id"] = ticket_category.id
        if max_per_user is not None: updates["ticket_config.max_tickets_per_user"] = max(1, min(10, max_per_user))
        if updates:
            await self.db.set_guild_config(interaction.guild.id, updates)
            await interaction.followup.send(embed=success_embed("Gespeichert", "Ticket-Einstellungen aktualisiert."), ephemeral=True)
        else:
            await interaction.followup.send(embed=info_embed("Keine Änderungen", "Keine Einstellungen angegeben."), ephemeral=True)


async def setup(bot):
    await bot.add_cog(TicketCommands(bot))
