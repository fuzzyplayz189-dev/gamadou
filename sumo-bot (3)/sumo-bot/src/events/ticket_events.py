"""
Ticket Events Cog — Bewertungssystem
"""
from __future__ import annotations
import discord
from discord.ext import commands
from datetime import datetime, timezone
from src.utils.embeds import base_embed, success_embed, BRAND_COLOR
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class RatingButton(discord.ui.Button):
    def __init__(self, stars: int, ticket: dict):
        super().__init__(label="⭐" * stars, style=discord.ButtonStyle.secondary,
                         custom_id=f"rating:{stars}:{ticket.get('ticket_id',0)}")
        self.stars = stars
        self.ticket = ticket

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ticket.get("creator_id"):
            await interaction.response.send_message("Nur der Ersteller kann bewerten.", ephemeral=True); return
        await interaction.response.send_modal(RatingModal(self.stars, self.ticket))


class RatingView(discord.ui.View):
    def __init__(self, ticket: dict):
        super().__init__(timeout=300)
        for stars in range(1, 6):
            self.add_item(RatingButton(stars, ticket))


class RatingModal(discord.ui.Modal):
    feedback = discord.ui.TextInput(label="Feedback (optional)", placeholder="Wie war deine Erfahrung?",
                                    style=discord.TextStyle.paragraph, required=False, max_length=500)

    def __init__(self, stars: int, ticket: dict):
        super().__init__(title=f"{'⭐' * stars} Support bewerten")
        self.stars = stars
        self.ticket = ticket

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.client.db.save_rating({
            "guild_id": interaction.guild.id,
            "ticket_id": self.ticket.get("ticket_id"),
            "creator_id": interaction.user.id,
            "staff_id": self.ticket.get("staff_id"),
            "stars": self.stars,
            "feedback": self.feedback.value,
            "created_at": datetime.now(timezone.utc),
        })
        embed = success_embed("Danke für dein Feedback!",
                              f"Du hast **{'⭐' * self.stars}** gegeben." +
                              (f"\n**Feedback:** {self.feedback.value}" if self.feedback.value else ""))
        await interaction.response.send_message(embed=embed, ephemeral=True)
        try:
            await interaction.message.edit(view=None)
        except Exception:
            pass


class TicketEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_rating_dm(self, guild: discord.Guild, ticket: dict):
        creator_id = ticket.get("creator_id")
        if not creator_id:
            return
        try:
            creator = guild.get_member(creator_id) or await self.bot.fetch_user(creator_id)
            if not creator:
                return
            embed = base_embed(
                title="🎫 Wie war dein Support-Erlebnis?",
                description=(f"Dein Ticket **#{str(ticket.get('ticket_id','?')).zfill(4)}** in **{guild.name}** "
                             f"wurde geschlossen.\nBitte bewerte deine Erfahrung!"),
                color=BRAND_COLOR,
            )
            await creator.send(embed=embed, view=RatingView(ticket=ticket))
        except (discord.Forbidden, discord.NotFound):
            pass


async def setup(bot):
    await bot.add_cog(TicketEvents(bot))
