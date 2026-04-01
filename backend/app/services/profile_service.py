from typing import Literal
from pydantic import BaseModel


class UserProfile(BaseModel):
    title: str | None = None
    date: str | None = None
    budget: int | None = None
    guests_count: int | None = None
    format: Literal["home", "restaurant", "outdoor", "mixed"] | None = None
    notes: str | None = None
    city: str | None = None


def _normalize_format(value: str | None) -> str | None:
    if not value:
        return None

    v = value.strip().lower()

    mapping = {
        "дом": "home",
        "дома": "home",
        "домашний": "home",
        "квартира": "home",

        "ресторан": "restaurant",
        "кафе": "restaurant",
        "банкет": "restaurant",
        "банкетный зал": "restaurant",
        "лофт": "restaurant",
        "караоке": "restaurant",

        "природа": "outdoor",
        "на природе": "outdoor",
        "улица": "outdoor",
        "парк": "outdoor",
        "загород": "outdoor",
        "база отдыха": "outdoor",

        "смешанный": "mixed",
        "mixed": "mixed",

        "home": "home",
        "restaurant": "restaurant",
        "outdoor": "outdoor",
    }

    return mapping.get(v, "mixed")


def collect_profile(event, current_user=None, db=None, latest_user_text=None) -> UserProfile:
    event_date = getattr(event, "date", None) or getattr(event, "event_date", None)
    guests_count = getattr(event, "guests_count", None) or getattr(event, "guests", None)
    notes = getattr(event, "notes", None) or getattr(event, "description", None)

    return UserProfile.model_validate(
        {
            "title": getattr(event, "title", None),
            "date": str(event_date) if event_date else None,
            "budget": getattr(event, "budget", None),
            "guests_count": guests_count,
            "format": _normalize_format(getattr(event, "format", None)),
            "notes": notes,
            "city": getattr(event, "city", None),
        }
    )