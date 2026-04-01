from datetime import date
from typing import List

from pydantic import BaseModel, field_validator

from .wishlist import WishlistOut


class EventCreate(BaseModel):
    title: str
    event_date: date | None = None
    budget: int | None = None
    guests_count: int | None = None
    format: str | None = None
    notes: str | None = None
    guest_emails: list[str] | None = None
    city: str | None = None
    status: str | None = None
    venue_mode: str | None = None
    selected_option: str | None = None
    selected_option_kind: str | None = None


class EventUpdate(BaseModel):
    title: str | None = None
    event_date: date | None = None
    budget: int | None = None
    guests_count: int | None = None
    format: str | None = None
    notes: str | None = None
    guest_emails: list[str] | None = None
    city: str | None = None
    status: str | None = None
    venue_mode: str | None = None
    selected_option: str | None = None
    selected_option_kind: str | None = None


class EventOut(BaseModel):
    id: int
    title: str
    event_date: date | None
    budget: int | None
    guests_count: int | None
    format: str | None
    notes: str | None
    city: str | None = None
    status: str | None = None
    venue_mode: str | None = None
    selected_option: str | None = None
    selected_option_kind: str | None = None
    owner_id: int
    google_calendar_link: str | None = None
    google_calendar_error: str | None = None
    guest_emails: list[str] | None = None
    google_invite_link: str | None = None
    wishlist_items: List[WishlistOut] | None = None

    model_config = {"from_attributes": True}

    @field_validator("guest_emails", mode="before")
    @classmethod
    def _parse_guest_emails(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(",") if p.strip()]
            return parts or None
        return None
