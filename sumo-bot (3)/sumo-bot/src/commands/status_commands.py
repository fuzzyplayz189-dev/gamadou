"""
Status Command Cog — /status
"""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from src.utils.embeds import success_embed
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class StatusCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="status", description="Ändert den Bot-Status")
    @app_commands.describe(activity_type="Aktivitäts-Typ", text="Aktivitäts-Text", status="Online-Status")
    @app_commands.choices(
        activity_type=[app_commands.Choice(name="🎮 Playing",   value="playing"),
                       app_commands.Choice(name="👀 Watching",  value="watching"),
                       app_commands.Choice(name="🎵 Listening", value="listening"),
                       app_commands.Choice(name="🏆 Competing", value="competing")],
        status=[app_commands.Choice(name="🟢 Online",    value="online"),
                app_commands.Choice(name="🟡 Idle",      value="idle"),
                app_commands.Choice(name="🔴 Bitte nicht stören", value="dnd"),
                app_commands.Choice(name="⚫ Unsichtbar", value="invisible")],
    )
    @app_commands.default_permissions(administrator=True)
    async def status(self, interaction: discord.Interaction, activity_type: str = "playing",
                     text: str = "Managing Tickets", status: str = "online"):
        await interaction.response.defer(ephemeral=True)
        atype = {"playing": discord.ActivityType.playing, "watching": discord.ActivityType.watching,
                 "listening": discord.ActivityType.listening, "competing": discord.ActivityType.competing}.get(activity_type, discord.ActivityType.playing)
        stype = {"online": discord.Status.online, "idle": discord.Status.idle,
                 "dnd": discord.Status.dnd, "invisible": discord.Status.invisible}.get(status, discord.Status.online)
        await self.bot.change_presence(status=stype, activity=discord.Activity(type=atype, name=text))
        await interaction.followup.send(embed=success_embed("Status aktualisiert",
            f"**Aktivität:** {activity_type.capitalize()} `{text}`\n**Status:** {status.capitalize()}"), ephemeral=True)


async def setup(bot):
    await bot.add_cog(StatusCommands(bot))
