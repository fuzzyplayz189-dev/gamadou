"""
Rating Service — Aggregiert Ticket-Bewertungen
"""
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class RatingService:
    def __init__(self, db):
        self.db = db

    async def get_staff_rating(self, guild_id: int, staff_id: int) -> dict:
        ratings = []
        for r in (await self.db.get_all_ratings(guild_id) if hasattr(self.db, "get_all_ratings") else []):
            if r.get("staff_id") == staff_id:
                ratings.append(r)
        if not ratings:
            return {"avg": 0.0, "count": 0}
        avg = sum(r["stars"] for r in ratings) / len(ratings)
        return {"avg": round(avg, 2), "count": len(ratings)}
