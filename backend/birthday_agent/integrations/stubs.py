from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from birthday_agent.integrations.base import IntegrationResult


@dataclass
class StubCalendar:
    def create_event_draft(self, *, title: str, start: datetime, end: datetime, description: str) -> IntegrationResult:
        return IntegrationResult(ok=True, details=f"[draft] calendar event: {title} {start.isoformat()}–{end.isoformat()}")


@dataclass
class StubMessenger:
    def send_invite(self, *, recipient: str, text: str) -> IntegrationResult:
        return IntegrationResult(ok=True, details=f"[stub] invite -> {recipient}: {text[:80]}")


@dataclass
class StubBooking:
    def create_booking_draft(self, *, venue_query: str, date_time: datetime, guests: int) -> IntegrationResult:
        return IntegrationResult(ok=True, details=f"[draft] booking: '{venue_query}' at {date_time.isoformat()} for {guests}")


@dataclass
class StubDelivery:
    def create_cart_draft(self, *, items: list[str], address: str) -> IntegrationResult:
        return IntegrationResult(ok=True, details=f"[draft] delivery cart to {address}: {len(items)} items")

