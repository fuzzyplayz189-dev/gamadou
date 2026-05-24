"""
Ticket Model
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Ticket:
    guild_id: int
    ticket_id: int
    channel_id: int
    creator_id: int
    creator_name: str
    category: str
    subject: str
    description: str
    priority: str = "medium"
    status: str = "open"
    staff_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    close_duration_seconds: Optional[float] = None
    transcript_url: Optional[str] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}
