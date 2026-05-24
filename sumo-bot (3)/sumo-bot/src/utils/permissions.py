"""
Permission Helpers
"""
import discord


def is_staff(member: discord.Member, config: dict) -> bool:
    staff_roles = config.get("staff_roles", [])
    return any(r.id in staff_roles for r in member.roles) or member.guild_permissions.manage_guild


def is_mod(member: discord.Member) -> bool:
    return member.guild_permissions.manage_messages or member.guild_permissions.administrator


def is_admin(member: discord.Member) -> bool:
    return member.guild_permissions.administrator
