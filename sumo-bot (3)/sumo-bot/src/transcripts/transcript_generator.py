"""
Transcript Generator — HTML, JSON, TXT
"""
from __future__ import annotations
import os
import json
import discord
from datetime import datetime, timezone
from typing import Optional
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TranscriptGenerator:
    def __init__(self, bot):
        self.bot = bot

    async def generate(self, channel: discord.TextChannel, requester, fmt: str = "html") -> Optional[str]:
        ticket = await self.bot.db.get_ticket_by_channel(channel.id)
        if not ticket:
            return None

        os.makedirs("transcripts", exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        tid = ticket.get("ticket_id", 0)

        messages = []
        async for msg in channel.history(limit=1000, oldest_first=True):
            messages.append({
                "id": msg.id, "author": str(msg.author), "author_id": msg.author.id,
                "content": msg.content, "timestamp": msg.created_at.isoformat(),
                "attachments": [a.url for a in msg.attachments],
                "embeds": len(msg.embeds),
            })

        if fmt == "json":
            path = f"transcripts/ticket-{tid:04d}-{ts}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"ticket": ticket, "messages": messages}, f, indent=2, default=str, ensure_ascii=False)
        elif fmt == "txt":
            path = f"transcripts/ticket-{tid:04d}-{ts}.txt"
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"Ticket #{str(tid).zfill(4)} — {ticket.get('subject','N/A')}\n")
                f.write("=" * 60 + "\n\n")
                for m in messages:
                    f.write(f"[{m['timestamp'][:19]}] {m['author']}: {m['content']}\n")
                    for att in m["attachments"]:
                        f.write(f"  📎 {att}\n")
        else:
            path = f"transcripts/ticket-{tid:04d}-{ts}.html"
            rows = ""
            for m in messages:
                ts_str = m["timestamp"][:19].replace("T", " ")
                content = m["content"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                atts = "".join(f'<a href="{a}" target="_blank">📎 Anhang</a>' for a in m["attachments"])
                rows += f'<div class="msg"><span class="ts">{ts_str}</span><span class="author">{m["author"]}</span><span class="content">{content}{atts}</span></div>\n'

            html = f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8">
<title>Ticket #{str(tid).zfill(4)}</title>
<style>
  body{{font-family:sans-serif;background:#36393f;color:#dcddde;margin:0;padding:20px}}
  h1{{color:#fff;border-bottom:2px solid #7289da;padding-bottom:10px}}
  .meta{{background:#2f3136;border-radius:8px;padding:15px;margin-bottom:20px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}}
  .meta span{{color:#b9bbbe;font-size:.9em}}.meta strong{{color:#fff}}
  .msg{{padding:8px 0;border-bottom:1px solid #40444b;display:flex;gap:10px;align-items:flex-start}}
  .ts{{color:#72767d;font-size:.8em;min-width:140px;white-space:nowrap}}
  .author{{color:#7289da;font-weight:bold;min-width:150px}}
  .content{{flex:1;word-break:break-word}}
  a{{color:#00b0f4}}
</style></head><body>
<h1>🎫 Ticket #{str(tid).zfill(4)}</h1>
<div class="meta">
  <span><strong>Kategorie</strong><br>{ticket.get('category','N/A')}</span>
  <span><strong>Ersteller</strong><br>{ticket.get('creator_name','N/A')}</span>
  <span><strong>Priorität</strong><br>{ticket.get('priority','N/A').capitalize()}</span>
  <span><strong>Betreff</strong><br>{ticket.get('subject','N/A')}</span>
  <span><strong>Status</strong><br>{ticket.get('status','N/A').capitalize()}</span>
  <span><strong>Nachrichten</strong><br>{len(messages)}</span>
</div>
{rows}
<footer style="color:#72767d;margin-top:20px;font-size:.8em">Erstellt von Sumo Bot • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</footer>
</body></html>"""
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)

        logger.info(f"Transcript erstellt: {path}")
        return path

    async def send_to_log_channel(self, guild, ticket, path):
        config = await self.bot.db.get_guild_config(guild.id)
        ch_id = config.get("ticket_log_channel_id")
        if not ch_id:
            return
        ch = guild.get_channel(ch_id)
        if ch:
            from src.utils.embeds import info_embed
            embed = info_embed("📜 Transcript gespeichert", f"Ticket #{str(ticket.get('ticket_id',0)).zfill(4)}")
            await ch.send(embed=embed, file=discord.File(path))
