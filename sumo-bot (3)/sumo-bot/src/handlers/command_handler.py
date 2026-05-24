"""
Command Handler — lädt alle Command-Cogs
"""
from discord.ext import commands
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

COGS = [
    "src.commands.ticket_commands",
    "src.commands.automod_commands",
    "src.commands.moderation_commands",
    "src.commands.setup_commands",
    "src.commands.status_commands",
    "src.commands.stats_commands",
]


class CommandHandler:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def load_cogs(self):
        for cog in COGS:
            try:
                await self.bot.load_extension(cog)
                logger.info(f"✓ Cog geladen: {cog}")
            except Exception as e:
                logger.error(f"✗ Fehler beim Laden von {cog}: {e}", exc_info=True)
