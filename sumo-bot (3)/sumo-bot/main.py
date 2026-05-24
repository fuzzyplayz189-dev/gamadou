"""
Sumo Bot — Main Entry Point
"""
import os
import sys
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

os.makedirs("logs", exist_ok=True)
os.makedirs("transcripts", exist_ok=True)
os.makedirs("data", exist_ok=True)

from src.utils.logger import setup_logger
from src.handlers.command_handler import CommandHandler
from src.handlers.event_handler import EventHandler
from src.database.db import Database

logger = setup_logger(__name__)


class SumoBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=os.getenv("PREFIX", "!"), intents=intents, help_command=None)
        self.db: Database = None
        self.command_handler = CommandHandler(self)
        self.event_handler = EventHandler(self)

    async def setup_hook(self):
        logger.info("Initialisiere Sumo Bot...")
        self.db = Database()
        await self.db.connect()

        await self.command_handler.load_cogs()
        await self.event_handler.load_events()

        dev_guild = os.getenv("DEV_GUILD_ID", "").strip()
        if dev_guild:
            guild = discord.Object(id=int(dev_guild))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"Commands in Dev-Guild {dev_guild} synchronisiert")
        else:
            await self.tree.sync()
            logger.info("Commands global synchronisiert (bis 1h Verzögerung möglich)")

    async def on_ready(self):
        logger.info(f"✅ Sumo Bot ist online als {self.user} (ID: {self.user.id})")
        logger.info(f"   {len(self.guilds)} Server | {len(self.users)} User")
        activity = discord.Game(name=os.getenv("DEFAULT_STATUS", "Managing Tickets"))
        await self.change_presence(status=discord.Status.online, activity=activity)

    async def on_error(self, event_method: str, *args, **kwargs):
        logger.error(f"Unbehandelter Fehler in {event_method}", exc_info=True)


async def main():
    bot = SumoBot()
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token or token == "DEIN_BOT_TOKEN_HIER":
        logger.critical("❌ BOT_TOKEN nicht gesetzt! Bitte .env Datei ausfüllen.")
        sys.exit(1)
    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
