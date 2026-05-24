"""
Premium Embed Utilities für Sumo Bot
"""
from __future__ import annotations
import discord
from datetime import datetime
from typing import Optional, Union

BRAND_COLOR   = discord.Color.from_rgb(88, 101, 242)
SUCCESS_COLOR = discord.Color.from_rgb(87, 242, 135)
ERROR_COLOR   = discord.Color.from_rgb(237, 66, 69)
WARNING_COLOR = discord.Color.from_rgb(254, 231, 92)
INFO_COLOR    = discord.Color.from_rgb(0, 176, 244)
TICKET_COLOR  = discord.Color.from_rgb(114, 137, 218)

EMOJI = {
    "ticket": "🎫", "success": "✅", "error": "❌", "warning": "⚠️",
    "info": "ℹ️", "claim": "🙋", "close": "🔒", "reopen": "🔓",
    "delete": "🗑️", "transcript": "📜", "star": "⭐", "shield": "🛡️",
    "ban": "🔨", "kick": "👢", "timeout": "⏱️", "warn": "⚠️",
    "automod": "🤖", "log": "📋", "stats": "📊",
    "priority_low": "🟢", "priority_medium": "🟡",
    "priority_high": "🔴", "priority_critical": "🚨",
}

PRIORITY_COLORS = {
    "low": discord.Color.green(), "medium": discord.Color.yellow(),
    "high": discord.Color.orange(), "critical": discord.Color.red(),
}
PRIORITY_EMOJI = {"low": "🟢", "medium": "🟡", "high": "🔴", "critical": "🚨"}


def _mention(obj) -> str:
    return obj.mention if hasattr(obj, "mention") else str(obj)

def _id(obj) -> str:
    return str(obj.id) if hasattr(obj, "id") else "N/A"

def _avatar(obj) -> Optional[str]:
    return str(obj.display_avatar.url) if hasattr(obj, "display_avatar") else None


def base_embed(title="", description="", color=BRAND_COLOR,
               footer=None, thumbnail=None, image=None,
               author_name=None, author_icon=None, timestamp=True) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    if timestamp:
        embed.timestamp = datetime.utcnow()
    embed.set_footer(text=footer or "Sumo Bot • Premium Support System")
    if thumbnail: embed.set_thumbnail(url=thumbnail)
    if image: embed.set_image(url=image)
    if author_name: embed.set_author(name=author_name, icon_url=author_icon)
    return embed

def success_embed(title: str, description: str = "") -> discord.Embed:
    return base_embed(f"{EMOJI['success']} {title}", description, SUCCESS_COLOR)

def error_embed(title: str, description: str = "") -> discord.Embed:
    return base_embed(f"{EMOJI['error']} {title}", description, ERROR_COLOR)

def warning_embed(title: str, description: str = "") -> discord.Embed:
    return base_embed(f"{EMOJI['warning']} {title}", description, WARNING_COLOR)

def info_embed(title: str, description: str = "") -> discord.Embed:
    return base_embed(f"{EMOJI['info']} {title}", description, INFO_COLOR)

def ticket_embed(ticket_id, category, creator, priority, status,
                 staff=None, subject="Kein Betreff", description="") -> discord.Embed:
    embed = base_embed(
        title=f"{EMOJI['ticket']} Ticket #{ticket_id}",
        description=f"```{description}```" if description else "",
        color=PRIORITY_COLORS.get(priority, TICKET_COLOR),
        thumbnail=_avatar(creator),
    )
    embed.add_field(name="👤 Ersteller",  value=_mention(creator), inline=True)
    embed.add_field(name="📂 Kategorie",  value=category, inline=True)
    embed.add_field(name=f"{PRIORITY_EMOJI.get(priority,'🟡')} Priorität", value=priority.capitalize(), inline=True)
    embed.add_field(name="📌 Betreff",    value=subject, inline=True)
    embed.add_field(name="🔄 Status",     value=status.capitalize(), inline=True)
    embed.add_field(name="🙋 Zuständig",  value=_mention(staff) if staff else "Nicht zugewiesen", inline=True)
    return embed

def mod_action_embed(action, target, moderator, reason, duration=None) -> discord.Embed:
    colors = {"ban": ERROR_COLOR, "kick": WARNING_COLOR, "timeout": WARNING_COLOR,
              "warn": WARNING_COLOR, "unban": SUCCESS_COLOR, "untimeout": SUCCESS_COLOR}
    embed = base_embed(
        f"{EMOJI.get(action.lower(), '🔨')} {action.upper()} | Moderations-Aktion",
        color=colors.get(action.lower(), BRAND_COLOR),
        thumbnail=_avatar(target),
    )
    embed.add_field(name="👤 Ziel",       value=f"{_mention(target)} (`{_id(target)}`)", inline=True)
    embed.add_field(name="🛡️ Moderator", value=f"{_mention(moderator)} (`{_id(moderator)}`)", inline=True)
    embed.add_field(name="📋 Grund",      value=reason or "Kein Grund angegeben", inline=False)
    if duration:
        embed.add_field(name="⏱️ Dauer", value=duration, inline=True)
    return embed

def automod_embed(rule_name, trigger_type, action, member=None, content=None) -> discord.Embed:
    embed = base_embed(f"{EMOJI['automod']} AutoMod Aktion", color=WARNING_COLOR)
    embed.add_field(name="📋 Regel",   value=rule_name, inline=True)
    embed.add_field(name="🎯 Trigger", value=trigger_type, inline=True)
    embed.add_field(name="⚡ Aktion",  value=action, inline=True)
    if member: embed.add_field(name="👤 Mitglied", value=_mention(member), inline=True)
    if content: embed.add_field(name="💬 Inhalt", value=f"||{content[:100]}||", inline=False)
    return embed

def stats_embed(title, stats: dict, color=BRAND_COLOR) -> discord.Embed:
    embed = base_embed(title, color=color)
    for k, v in stats.items():
        embed.add_field(name=k, value=str(v), inline=True)
    return embed
