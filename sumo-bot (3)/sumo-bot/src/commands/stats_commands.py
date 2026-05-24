"""
Stats Commands Cog — /botstats /serverinfo /userinfo
"""
from __future__ import annotations
import os
import discord
from datetime import datetime, timezone
from discord.ext import commands
from discord import app_commands
from src.utils.embeds import base_embed, BRAND_COLOR
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


class StatsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._start = datetime.now(timezone.utc)

    @app_commands.command(name="botstats", description="Bot-Statistiken")
    async def botstats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        uptime = datetime.now(timezone.utc) - self._start
        h, rem = divmod(int(uptime.total_seconds()), 3600)
        m, s = divmod(rem, 60)
        embed = base_embed("📊 Sumo Bot Statistiken", color=BRAND_COLOR,
                           thumbnail=str(self.bot.user.display_avatar.url) if self.bot.user else None)
        embed.add_field(name="🤖 Bot",     value=str(self.bot.user), inline=True)
        embed.add_field(name="🏠 Server",  value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="👥 User",    value=str(len(self.bot.users)), inline=True)
        embed.add_field(name="⏱️ Uptime", value=f"{h}h {m}m {s}s", inline=True)
        embed.add_field(name="📡 Latenz",  value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="📦 Version", value="1.0.0", inline=True)
        if _HAS_PSUTIL:
            proc = psutil.Process(os.getpid())
            embed.add_field(name="🧠 RAM", value=f"{proc.memory_info().rss / 1024 / 1024:.1f} MB", inline=True)
            embed.add_field(name="💻 CPU", value=f"{psutil.cpu_percent(interval=None)}%", inline=True)
        embed.add_field(name="🐍 Library", value="discord.py 2.4+", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="serverinfo", description="Server-Informationen")
    async def serverinfo(self, interaction: discord.Interaction):
        g = interaction.guild
        embed = base_embed(f"🏠 {g.name}", color=BRAND_COLOR, thumbnail=str(g.icon.url) if g.icon else None)
        embed.add_field(name="👑 Eigentümer",   value=g.owner.mention if g.owner else "N/A", inline=True)
        embed.add_field(name="🆔 Server-ID",    value=f"`{g.id}`", inline=True)
        embed.add_field(name="📅 Erstellt",     value=g.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="👥 Mitglieder",   value=str(g.member_count), inline=True)
        embed.add_field(name="💬 Kanäle",       value=str(len(g.channels)), inline=True)
        embed.add_field(name="🎭 Rollen",       value=str(len(g.roles)), inline=True)
        embed.add_field(name="🚀 Boosts",       value=str(g.premium_subscription_count), inline=True)
        embed.add_field(name="🔒 Verifikation", value=str(g.verification_level).capitalize(), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="User-Informationen")
    @app_commands.describe(member="Mitglied")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        m = member or interaction.user
        embed = base_embed(f"👤 {m}", color=m.color if m.color.value else BRAND_COLOR,
                           thumbnail=str(m.display_avatar.url))
        embed.add_field(name="🆔 User-ID",         value=f"`{m.id}`", inline=True)
        embed.add_field(name="📅 Account erstellt", value=m.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="📥 Beigetreten",      value=m.joined_at.strftime("%Y-%m-%d") if m.joined_at else "N/A", inline=True)
        embed.add_field(name="🎭 Höchste Rolle",    value=m.top_role.mention, inline=True)
        embed.add_field(name="🔢 Rollen",           value=str(len(m.roles) - 1), inline=True)
        embed.add_field(name="🤖 Bot",              value="Ja" if m.bot else "Nein", inline=True)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(StatsCommands(bot))
