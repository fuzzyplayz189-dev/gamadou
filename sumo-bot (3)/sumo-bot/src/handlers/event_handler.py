"""
Event Handler — lädt alle Event-Cogs
"""
from discord.ext import commands
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

EVENT_COGS = [
    "src.events.ticket_events",
    "src.events.automod_events",
    "src.events.log_events",
    "src.events.moderation_events",
]


class EventHandler:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def load_events(self):
        for cog in EVENT_COGS:
            try:
                await self.bot.load_extension(cog)
                logger.info(f"✓ Event-Cog geladen: {cog}")
            except Exception as e:
                logger.error(f"✗ Fehler beim Laden von {cog}: {e}", exc_info=True)
