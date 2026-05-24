"""
Ticket Panel System
"""
from __future__ import annotations
import discord
from datetime import datetime, timezone
from src.utils.embeds import base_embed, BRAND_COLOR, EMOJI
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TicketOpenModal(discord.ui.Modal):
    subject = discord.ui.TextInput(label="Betreff", placeholder="Kurze Zusammenfassung...",
                                   style=discord.TextStyle.short, required=True, max_length=100)
    description = discord.ui.TextInput(label="Beschreibung", placeholder="Beschreibe dein Problem detailliert...",
                                       style=discord.TextStyle.paragraph, required=True, max_length=1000)
    priority = discord.ui.TextInput(label="Priorität (low / medium / high / critical)",
                                    placeholder="medium", style=discord.TextStyle.short, required=False, max_length=10)
    additional = discord.ui.TextInput(label="Zusätzliche Informationen (optional)",
                                      placeholder="Links, Screenshots...", style=discord.TextStyle.paragraph,
                                      required=False, max_length=500)

    def __init__(self, category: dict):
        super().__init__(title=f"Ticket öffnen — {category['name'][:40]}")
        self.category = category

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        priority = (self.priority.value or "medium").strip().lower()
        if priority not in {"low", "medium", "high", "critical"}:
            priority = "medium"
        full_desc = self.description.value
        if self.additional.value:
            full_desc += f"\n\n**Zusätzliche Info:**\n{self.additional.value}"

        from src.tickets.ticket_manager import TicketManager
        channel, error = await TicketManager(interaction.client).create_ticket(
            guild=interaction.guild, creator=interaction.user, category=self.category,
            subject=self.subject.value, description=full_desc, priority=priority,
        )
        if error:
            await interaction.followup.send(f"❌ {error}", ephemeral=True)
        else:
            await interaction.followup.send(f"✅ Ticket erstellt: {channel.mention}", ephemeral=True)


class TicketCategoryButton(discord.ui.Button):
    def __init__(self, category: dict, row: int = 0):
        super().__init__(label=category["name"][:80], emoji=category.get("emoji", "🎫"),
                         style=discord.ButtonStyle.primary,
                         custom_id=f"panel:cat:{category['name'][:40].replace(' ','_')}", row=row)
        self.category = category

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketOpenModal(self.category))


class TicketCategorySelect(discord.ui.Select):
    def __init__(self, categories: list):
        options = [discord.SelectOption(label=c["name"][:100], description=c.get("description","")[:100],
                                        emoji=c.get("emoji","🎫"), value=c["name"][:100]) for c in categories[:25]]
        super().__init__(placeholder="📂 Kategorie auswählen...", options=options, custom_id="panel:cat_select")
        self.cats = {c["name"]: c for c in categories}

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketOpenModal(self.cats.get(self.values[0], {})))


class TicketPanelView(discord.ui.View):
    def __init__(self, categories: list, panel_type: str = "buttons"):
        super().__init__(timeout=None)
        if panel_type == "select":
            self.add_item(TicketCategorySelect(categories))
        else:
            for i, cat in enumerate(categories[:20]):
                self.add_item(TicketCategoryButton(cat, row=min(i // 5, 4)))


class PanelManager:
    def __init__(self, bot):
        self.bot = bot

    async def create_panel(self, channel, title, description, categories, panel_type="buttons", color=BRAND_COLOR):
        embed = base_embed(title=f"{EMOJI['ticket']} {title}", description=description, color=color)
        lines = "\n".join(f"{c.get('emoji','🎫')} **{c['name']}** — {c.get('description','')}" for c in categories)
        embed.add_field(name="Verfügbare Kategorien", value=lines or "Keine Kategorien", inline=False)
        embed.set_footer(text="Klicke auf einen Button • Sumo Support")
        view = TicketPanelView(categories=categories, panel_type=panel_type)
        msg = await channel.send(embed=embed, view=view)
        await self.bot.db.update_guild_config(channel.guild.id, f"panels.{msg.id}", {
            "message_id": msg.id, "channel_id": channel.id,
            "title": title, "categories": categories, "panel_type": panel_type,
            "created_at": datetime.now(timezone.utc),
        })
        return msg
