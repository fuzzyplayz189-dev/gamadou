"""
Ticket Manager — Lifecycle: Erstellen, Schließen, Claimen, Löschen
"""
from __future__ import annotations
import discord
from datetime import datetime, timezone
from typing import Optional
from src.utils.embeds import ticket_embed, success_embed, error_embed, EMOJI
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TicketManager:
    def __init__(self, bot):
        self.bot = bot

    @property
    def db(self):
        return self.bot.db

    async def create_ticket(self, guild, creator, category, subject, description, priority="medium"):
        config = await self.db.get_guild_config(guild.id)
        max_t = config.get("ticket_config", {}).get("max_tickets_per_user", 3)
        open_t = await self.db.get_user_open_tickets(guild.id, creator.id)
        if len(open_t) >= max_t:
            return None, f"Du hast bereits {len(open_t)} offene Ticket(s). Schließe bestehende zuerst."

        ticket_id = await self.db.get_next_ticket_id(guild.id)
        cat_name = category.get("name", "Support")
        staff_roles = category.get("staff_roles", [])

        parent_id = config.get("ticket_config", {}).get("ticket_category_id")
        parent = guild.get_channel(parent_id) if parent_id else None

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            creator: discord.PermissionOverwrite(view_channel=True, send_messages=True,
                                                  read_message_history=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True,
                                                   manage_channels=True, manage_messages=True,
                                                   read_message_history=True, attach_files=True, embed_links=True),
        }
        for rid in staff_roles:
            role = guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True,
                                                                read_message_history=True, attach_files=True,
                                                                embed_links=True, manage_messages=True)
        try:
            channel = await guild.create_text_channel(
                name=f"ticket-{ticket_id:04d}-{creator.name[:10].lower()}",
                category=parent, overwrites=overwrites,
                topic=f"Ticket #{ticket_id} | {creator} | {cat_name} | {priority.upper()}",
            )
        except discord.Forbidden:
            return None, "Keine Berechtigung, Ticket-Kanäle zu erstellen."

        now = datetime.now(timezone.utc)
        await self.db.create_ticket({
            "guild_id": guild.id, "ticket_id": ticket_id, "channel_id": channel.id,
            "creator_id": creator.id, "creator_name": str(creator),
            "category": cat_name, "subject": subject, "description": description,
            "priority": priority, "status": "open", "staff_id": None,
            "created_at": now, "closed_at": None, "close_duration_seconds": None,
        })
        await self._send_header(channel, ticket_id, creator, cat_name, subject, description, priority)
        logger.info(f"Ticket #{ticket_id} erstellt von {creator} in Guild {guild.id}")
        return channel, None

    async def _send_header(self, channel, ticket_id, creator, category, subject, description, priority):
        embed = ticket_embed(str(ticket_id).zfill(4), category, creator, priority, "Open", subject=subject, description=description)
        embed.description = (f"Willkommen {creator.mention}! Dein Ticket wurde erstellt.\n"
                             f"Beschreibe dein Problem detailliert — das Staff-Team hilft dir bald.\n\n"
                             f"> Nutze die Buttons unten zur Verwaltung.")
        view = TicketControlView(ticket_id=ticket_id, creator_id=creator.id)
        msg = await channel.send(embed=embed, view=view)
        await msg.pin()

    async def close_ticket(self, channel, closer, reason="Kein Grund"):
        ticket = await self.db.get_ticket_by_channel(channel.id)
        if not ticket or ticket["status"] != "open":
            return False
        now = datetime.now(timezone.utc)
        created = ticket["created_at"]
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        duration = (now - created).total_seconds()
        await self.db.update_ticket(ticket["guild_id"], ticket["ticket_id"], {
            "status": "closed", "closed_at": now,
            "close_duration_seconds": duration,
            "closed_by": closer.id, "close_reason": reason,
        })
        creator = channel.guild.get_member(ticket["creator_id"])
        if creator:
            await channel.set_permissions(creator, view_channel=False)
        await channel.send(embed=success_embed("Ticket geschlossen",
                                               f"Von {closer.mention} geschlossen.\n**Grund:** {reason}"),
                           view=ClosedTicketView(ticket_id=ticket["ticket_id"]))
        await channel.edit(name=f"closed-{ticket['ticket_id']:04d}")
        return True

    async def claim_ticket(self, channel, staff):
        ticket = await self.db.get_ticket_by_channel(channel.id)
        if not ticket or ticket["status"] != "open":
            return False
        await self.db.update_ticket(ticket["guild_id"], ticket["ticket_id"],
                                    {"staff_id": staff.id, "staff_name": str(staff),
                                     "claimed_at": datetime.now(timezone.utc)})
        await channel.send(embed=success_embed("Ticket übernommen", f"🙋 {staff.mention} hat dieses Ticket übernommen."))
        return True

    async def delete_ticket(self, channel, deleter):
        ticket = await self.db.get_ticket_by_channel(channel.id)
        if not ticket:
            return False
        await self.db.update_ticket(ticket["guild_id"], ticket["ticket_id"],
                                    {"status": "deleted", "deleted_by": deleter.id,
                                     "deleted_at": datetime.now(timezone.utc)})
        await channel.delete(reason=f"Gelöscht von {deleter}")
        return True

    async def set_priority(self, channel, priority):
        ticket = await self.db.get_ticket_by_channel(channel.id)
        if not ticket:
            return False
        await self.db.update_ticket(ticket["guild_id"], ticket["ticket_id"], {"priority": priority})
        return True

    async def add_user(self, channel, member):
        await channel.set_permissions(member, view_channel=True, send_messages=True, read_message_history=True)

    async def remove_user(self, channel, member):
        await channel.set_permissions(member, overwrite=None)


# ─── Views ────────────────────────────────────────────────────────────────────

class TicketControlView(discord.ui.View):
    def __init__(self, ticket_id: int, creator_id: int):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
        self.creator_id = creator_id

    @discord.ui.button(label="Claim", emoji="🙋", style=discord.ButtonStyle.primary, custom_id="ticket:claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True); return
        success = await TicketManager(interaction.client).claim_ticket(interaction.channel, interaction.user)
        if not success:
            await interaction.response.send_message("❌ Konnte nicht übernommen werden.", ephemeral=True)
        else:
            await interaction.response.send_message(f"✅ Übernommen von {interaction.user.mention}.")

    @discord.ui.button(label="Schließen", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="ticket:close")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CloseTicketModal())

    @discord.ui.button(label="Transcript", emoji="📜", style=discord.ButtonStyle.secondary, custom_id="ticket:transcript")
    async def transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        from src.transcripts.transcript_generator import TranscriptGenerator
        path = await TranscriptGenerator(interaction.client).generate(interaction.channel, interaction.user)
        if path:
            await interaction.followup.send("📜 Transcript:", file=discord.File(path), ephemeral=True)
        else:
            await interaction.followup.send("❌ Kein Ticket-Kanal.", ephemeral=True)

    @discord.ui.button(label="User hinzufügen", emoji="➕", style=discord.ButtonStyle.secondary, custom_id="ticket:add_user")
    async def add_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddUserModal())

    @discord.ui.button(label="Priorität", emoji="🎯", style=discord.ButtonStyle.secondary, custom_id="ticket:priority")
    async def priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Priorität wählen:", view=PrioritySelectView(), ephemeral=True)


class ClosedTicketView(discord.ui.View):
    def __init__(self, ticket_id: int):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id

    @discord.ui.button(label="Wiedereröffnen", emoji="🔓", style=discord.ButtonStyle.success, custom_id="ticket:reopen")
    async def reopen(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket = await interaction.client.db.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            await interaction.response.send_message("❌ Ticket nicht gefunden.", ephemeral=True); return
        creator = interaction.guild.get_member(ticket["creator_id"])
        if creator:
            await interaction.channel.set_permissions(creator, view_channel=True, send_messages=True, read_message_history=True)
        await interaction.client.db.update_ticket(interaction.guild.id, ticket["ticket_id"], {"status": "open"})
        await interaction.channel.edit(name=f"ticket-{ticket['ticket_id']:04d}")
        await interaction.response.send_message(f"🔓 Wiedereröffnet von {interaction.user.mention}.")

    @discord.ui.button(label="Löschen", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="ticket:delete")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True); return
        await interaction.response.send_message("🗑️ Kanal wird in 5 Sekunden gelöscht...")
        import asyncio; await asyncio.sleep(5)
        await TicketManager(interaction.client).delete_ticket(interaction.channel, interaction.user)


class CloseTicketModal(discord.ui.Modal, title="Ticket schließen"):
    reason = discord.ui.TextInput(label="Grund", placeholder="Warum wird das Ticket geschlossen?",
                                  style=discord.TextStyle.paragraph, required=False, max_length=500)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await TicketManager(interaction.client).close_ticket(
            interaction.channel, interaction.user, self.reason.value or "Kein Grund angegeben")


class AddUserModal(discord.ui.Modal, title="User hinzufügen"):
    user_id = discord.ui.TextInput(label="User ID", placeholder="Discord User ID...",
                                   style=discord.TextStyle.short, required=True, max_length=30)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            member = interaction.guild.get_member(int(self.user_id.value))
            if not member:
                await interaction.response.send_message("❌ User nicht gefunden.", ephemeral=True); return
            await TicketManager(interaction.client).add_user(interaction.channel, member)
            await interaction.response.send_message(f"✅ {member.mention} hinzugefügt.")
        except ValueError:
            await interaction.response.send_message("❌ Ungültige User ID.", ephemeral=True)


class PrioritySelectView(discord.ui.View):
    @discord.ui.select(placeholder="Priorität wählen...", options=[
        discord.SelectOption(label="Niedrig",   value="low",      emoji="🟢"),
        discord.SelectOption(label="Mittel",    value="medium",   emoji="🟡"),
        discord.SelectOption(label="Hoch",      value="high",     emoji="🔴"),
        discord.SelectOption(label="Kritisch",  value="critical", emoji="🚨"),
    ])
    async def select_priority(self, interaction: discord.Interaction, select: discord.ui.Select):
        await TicketManager(interaction.client).set_priority(interaction.channel, select.values[0])
        await interaction.response.send_message(f"✅ Priorität: **{select.values[0].capitalize()}**", ephemeral=True)
