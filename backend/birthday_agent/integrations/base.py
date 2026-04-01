from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class IntegrationResult:
    ok: bool
    details: str


class CalendarIntegration(Protocol):
    def create_event_draft(self, *, title: str, start: datetime, end: datetime, description: str) -> IntegrationResult: ...


class MessengerIntegration(Protocol):
    def send_invite(self, *, recipient: str, text: str) -> IntegrationResult: ...


class BookingIntegration(Protocol):
    def create_booking_draft(self, *, venue_query: str, date_time: datetime, guests: int) -> IntegrationResult: ...


class DeliveryIntegration(Protocol):
    def create_cart_draft(self, *, items: list[str], address: str) -> IntegrationResult: ...

