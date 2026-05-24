"""
Standard-Konfiguration
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class DefaultTicketConfig:
    max_tickets_per_user: int = 3
    transcript_format: str = "html"
    default_categories: List[dict] = field(default_factory=lambda: [
        {
            "name": "Allgemeiner Support",
            "description": "Fragen und allgemeine Hilfe",
            "emoji": "💬",
            "staff_roles": [],
            "welcome_message": "Willkommen! Beschreibe bitte dein Anliegen.",
        },
        {
            "name": "Technischer Support",
            "description": "Technische Probleme und Bugs",
            "emoji": "🔧",
            "staff_roles": [],
            "welcome_message": "Beschreibe das technische Problem so genau wie möglich.",
        },
        {
            "name": "Bewerbung",
            "description": "Team-Bewerbungen",
            "emoji": "📋",
            "staff_roles": [],
            "welcome_message": "Vielen Dank für deine Bewerbung! Wir melden uns bald.",
        },
        {
            "name": "Report",
            "description": "Mitglieder oder Verstöße melden",
            "emoji": "🚨",
            "staff_roles": [],
            "welcome_message": "Beschreibe den Vorfall mit allen relevanten Details.",
        },
    ])


DEFAULT_TICKET_CONFIG = DefaultTicketConfig()
