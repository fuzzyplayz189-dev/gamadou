"""
Sumo Bot — Datenbank
Verwendet standardmäßig eine lokale JSON-Datenbank (kein Setup nötig).
Optional: MongoDB via MONGODB_URI in .env aktivieren.
"""

from __future__ import annotations
import os
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# ─── Versuche motor zu importieren (optional) ─────────────────────────────────
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    _MOTOR_AVAILABLE = True
except ImportError:
    _MOTOR_AVAILABLE = False


# ─── JSON Datenbank ───────────────────────────────────────────────────────────

class JsonDatabase:
    """Einfache dateibasierte Datenbank — kein MongoDB nötig."""

    def __init__(self, data_dir: str = "data"):
        self._dir = Path(data_dir)
        self._dir.mkdir(exist_ok=True)
        self._lock = asyncio.Lock()
        logger.info(f"JSON-Datenbank initialisiert: {self._dir.resolve()}")

    def _path(self, guild_id: int) -> Path:
        return self._dir / f"{guild_id}.json"

    def _read(self, guild_id: int) -> dict:
        p = self._path(guild_id)
        if not p.exists():
            return self._default()
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return self._default()

    def _write(self, guild_id: int, data: dict):
        self._path(guild_id).write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    @staticmethod
    def _default() -> dict:
        return {
            "config": {},
            "tickets": {},
            "ticket_counter": 0,
            "warnings": [],
            "mod_logs": [],
            "automod_rules": [],
            "ratings": [],
            "panels": {},
        }

    # ─── Config ───────────────────────────────────────────────────────────────

    async def get_guild_config(self, guild_id: int) -> dict:
        async with self._lock:
            return self._read(guild_id).get("config", {})

    async def set_guild_config(self, guild_id: int, updates: dict):
        async with self._lock:
            data = self._read(guild_id)
            data["config"].update(updates)
            self._write(guild_id, data)

    async def update_guild_config(self, guild_id: int, key: str, value: Any):
        async with self._lock:
            data = self._read(guild_id)
            data["config"][key] = value
            self._write(guild_id, data)

    # ─── Tickets ──────────────────────────────────────────────────────────────

    async def get_next_ticket_id(self, guild_id: int) -> int:
        async with self._lock:
            data = self._read(guild_id)
            data["ticket_counter"] = data.get("ticket_counter", 0) + 1
            self._write(guild_id, data)
            return data["ticket_counter"]

    async def create_ticket(self, ticket_data: dict):
        gid = ticket_data["guild_id"]
        tid = str(ticket_data["ticket_id"])
        async with self._lock:
            data = self._read(gid)
            data["tickets"][tid] = ticket_data
            self._write(gid, data)

    async def get_ticket_by_channel(self, channel_id: int) -> Optional[dict]:
        # Scan across guild files
        for path in self._dir.glob("*.json"):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                for t in raw.get("tickets", {}).values():
                    if t.get("channel_id") == channel_id:
                        return t
            except Exception:
                continue
        return None

    async def get_user_open_tickets(self, guild_id: int, user_id: int) -> list:
        async with self._lock:
            data = self._read(guild_id)
            return [t for t in data["tickets"].values()
                    if t.get("creator_id") == user_id and t.get("status") == "open"]

    async def update_ticket(self, guild_id: int, ticket_id: int, updates: dict):
        tid = str(ticket_id)
        async with self._lock:
            data = self._read(guild_id)
            if tid in data["tickets"]:
                data["tickets"][tid].update(updates)
                self._write(guild_id, data)

    async def get_guild_tickets(self, guild_id: int) -> list:
        async with self._lock:
            return list(self._read(guild_id).get("tickets", {}).values())

    async def get_ticket_stats(self, guild_id: int) -> dict:
        tickets = await self.get_guild_tickets(guild_id)
        open_t   = [t for t in tickets if t.get("status") == "open"]
        closed_t = [t for t in tickets if t.get("status") == "closed"]
        durations = [t["close_duration_seconds"] for t in closed_t if t.get("close_duration_seconds")]
        avg = sum(durations) / len(durations) if durations else 0
        return {
            "total":          len(tickets),
            "open":           len(open_t),
            "closed":         len(closed_t),
            "avg_close_time": avg,
        }

    # ─── Verwarnungen ─────────────────────────────────────────────────────────

    async def add_warning(self, warning: dict):
        gid = warning["guild_id"]
        async with self._lock:
            data = self._read(gid)
            data["warnings"].append(warning)
            self._write(gid, data)

    async def get_warnings(self, guild_id: int, user_id: int) -> list:
        async with self._lock:
            data = self._read(guild_id)
            return [w for w in data["warnings"] if w.get("user_id") == user_id]

    async def clear_warnings(self, guild_id: int, user_id: int) -> int:
        async with self._lock:
            data = self._read(guild_id)
            before = len(data["warnings"])
            data["warnings"] = [w for w in data["warnings"] if w.get("user_id") != user_id]
            count = before - len(data["warnings"])
            self._write(guild_id, data)
            return count

    # ─── Mod Logs ─────────────────────────────────────────────────────────────

    async def add_mod_log(self, log: dict):
        gid = log["guild_id"]
        async with self._lock:
            data = self._read(gid)
            data["mod_logs"].append(log)
            self._write(gid, data)

    async def get_mod_logs(self, guild_id: int, user_id: int) -> list:
        async with self._lock:
            data = self._read(guild_id)
            return [l for l in data["mod_logs"] if l.get("target_id") == user_id]

    # ─── AutoMod ──────────────────────────────────────────────────────────────

    async def save_automod_rule(self, rule: dict):
        gid = rule["guild_id"]
        async with self._lock:
            data = self._read(gid)
            data["automod_rules"] = [r for r in data["automod_rules"] if r.get("rule_id") != rule.get("rule_id")]
            data["automod_rules"].append(rule)
            self._write(gid, data)

    async def delete_automod_rule(self, guild_id: int, rule_id: str):
        async with self._lock:
            data = self._read(guild_id)
            data["automod_rules"] = [r for r in data["automod_rules"] if r.get("rule_id") != rule_id]
            self._write(guild_id, data)

    # ─── Bewertungen ──────────────────────────────────────────────────────────

    async def save_rating(self, rating: dict):
        gid = rating["guild_id"]
        async with self._lock:
            data = self._read(gid)
            data["ratings"].append(rating)
            self._write(gid, data)

    async def connect(self):
        logger.info("JSON-Datenbank bereit (kein MongoDB nötig)")

    async def disconnect(self):
        pass


# ─── MongoDB Datenbank ────────────────────────────────────────────────────────

class MongoDatabase:
    """MongoDB-Datenbank via MONGODB_URI."""

    def __init__(self, uri: str, db_name: str = "sumobot"):
        from motor.motor_asyncio import AsyncIOMotorClient
        self._client = AsyncIOMotorClient(uri)
        self._db = self._client[db_name]

    async def connect(self):
        await self._client.admin.command("ping")
        logger.info("MongoDB verbunden")

    async def disconnect(self):
        self._client.close()

    async def get_guild_config(self, guild_id: int) -> dict:
        doc = await self._db.guild_configs.find_one({"guild_id": guild_id})
        return doc or {}

    async def set_guild_config(self, guild_id: int, updates: dict):
        await self._db.guild_configs.update_one(
            {"guild_id": guild_id}, {"$set": updates}, upsert=True
        )

    async def update_guild_config(self, guild_id: int, key: str, value: Any):
        await self._db.guild_configs.update_one(
            {"guild_id": guild_id}, {"$set": {key: value}}, upsert=True
        )

    async def get_next_ticket_id(self, guild_id: int) -> int:
        result = await self._db.guild_configs.find_one_and_update(
            {"guild_id": guild_id},
            {"$inc": {"ticket_counter": 1}},
            upsert=True, return_document=True,
        )
        return result.get("ticket_counter", 1)

    async def create_ticket(self, ticket_data: dict):
        await self._db.tickets.insert_one(ticket_data)

    async def get_ticket_by_channel(self, channel_id: int) -> Optional[dict]:
        return await self._db.tickets.find_one({"channel_id": channel_id})

    async def get_user_open_tickets(self, guild_id: int, user_id: int) -> list:
        cursor = self._db.tickets.find({"guild_id": guild_id, "creator_id": user_id, "status": "open"})
        return await cursor.to_list(length=100)

    async def update_ticket(self, guild_id: int, ticket_id: int, updates: dict):
        await self._db.tickets.update_one({"guild_id": guild_id, "ticket_id": ticket_id}, {"$set": updates})

    async def get_guild_tickets(self, guild_id: int) -> list:
        cursor = self._db.tickets.find({"guild_id": guild_id}).sort("ticket_id", -1).limit(50)
        return await cursor.to_list(length=50)

    async def get_ticket_stats(self, guild_id: int) -> dict:
        pipeline = [
            {"$match": {"guild_id": guild_id}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "avg_duration": {"$avg": "$close_duration_seconds"},
            }},
        ]
        results = await self._db.tickets.aggregate(pipeline).to_list(length=10)
        stats = {"total": 0, "open": 0, "closed": 0, "avg_close_time": 0}
        for r in results:
            stats["total"] += r["count"]
            stats[r["_id"]] = r["count"]
            if r["_id"] == "closed":
                stats["avg_close_time"] = r.get("avg_duration") or 0
        return stats

    async def add_warning(self, warning: dict):
        await self._db.warnings.insert_one(warning)

    async def get_warnings(self, guild_id: int, user_id: int) -> list:
        cursor = self._db.warnings.find({"guild_id": guild_id, "user_id": user_id})
        return await cursor.to_list(length=100)

    async def clear_warnings(self, guild_id: int, user_id: int) -> int:
        result = await self._db.warnings.delete_many({"guild_id": guild_id, "user_id": user_id})
        return result.deleted_count

    async def add_mod_log(self, log: dict):
        await self._db.mod_logs.insert_one(log)

    async def get_mod_logs(self, guild_id: int, user_id: int) -> list:
        cursor = self._db.mod_logs.find({"guild_id": guild_id, "target_id": user_id}).sort("created_at", -1).limit(20)
        return await cursor.to_list(length=20)

    async def save_automod_rule(self, rule: dict):
        await self._db.automod_rules.update_one(
            {"guild_id": rule["guild_id"], "rule_id": rule["rule_id"]},
            {"$set": rule}, upsert=True,
        )

    async def delete_automod_rule(self, guild_id: int, rule_id: str):
        await self._db.automod_rules.delete_one({"guild_id": guild_id, "rule_id": rule_id})

    async def save_rating(self, rating: dict):
        await self._db.ratings.insert_one(rating)


# ─── Factory ──────────────────────────────────────────────────────────────────

class Database:
    """
    Automatische Datenbank-Auswahl:
    - MONGODB_URI gesetzt + motor installiert → MongoDB
    - Alles andere                            → JSON-Dateien (data/ Ordner)
    """

    def __new__(cls) -> "JsonDatabase | MongoDatabase":
        mongo_uri = os.getenv("MONGODB_URI", "").strip()
        if mongo_uri and _MOTOR_AVAILABLE:
            logger.info("Verwende MongoDB")
            return MongoDatabase(mongo_uri)
        if mongo_uri and not _MOTOR_AVAILABLE:
            logger.warning("MONGODB_URI gesetzt, aber 'motor' nicht installiert → JSON-Fallback")
        logger.info("Verwende JSON-Datenbank (data/ Ordner)")
        return JsonDatabase()
