from __future__ import annotations

from datetime import date, timedelta
from urllib.parse import urlencode
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings
from app.models.event import Event
from app.models.user import User

SCOPES = ["https://www.googleapis.com/auth/calendar"]


_calendar_service = None


def _get_service():
    global _calendar_service
    if _calendar_service is not None:
        return _calendar_service

    if not settings.GOOGLE_CALENDAR_ENABLED:
        return None
    if not settings.GOOGLE_SERVICE_ACCOUNT_FILE:
        return None

    creds = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )
    _calendar_service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    return _calendar_service


def create_calendar_event_for_event(
    event: Event,
    owner: User,
) -> Optional[str]:
    """
    Create a Google Calendar event for our domain Event.

    Returns HTML link to the calendar event, if created.
    """
    if not settings.GOOGLE_CALENDAR_ENABLED:
        return None
    if not settings.GOOGLE_CALENDAR_ID:
        return None

    service = _get_service()
    if service is None:
        return None

    # If date is missing, still create a placeholder on today's date so users
    # can see it and later adjust in Calendar.
    start_date: date = event.event_date or date.today()
    end_date = start_date + timedelta(days=1)

    summary = event.title
    description_parts: list[str] = []
    if event.format:
        description_parts.append(f"Формат: {event.format}")
    if event.guests_count is not None:
        description_parts.append(f"Гостей: {event.guests_count}")
    if event.budget is not None:
        description_parts.append(f"Бюджет: {event.budget} ₽")
    if event.notes:
        description_parts.append("")
        description_parts.append(event.notes)
    description = "\n".join(description_parts) if description_parts else ""

    body = {
        "summary": summary,
        "description": description or None,
        "start": {
            "date": start_date.isoformat(),
            "timeZone": settings.GOOGLE_TIMEZONE,
        },
        "end": {
            "date": end_date.isoformat(),
            "timeZone": settings.GOOGLE_TIMEZONE,
        },
    }

    # NOTE: For consumer Google accounts, service accounts are not allowed to
    # invite attendees unless you use Google Workspace + Domain-Wide Delegation.
    # Creating the event directly in the shared calendar is enough.

    created = (
        service.events()
        .insert(
            calendarId=settings.GOOGLE_CALENDAR_ID,
            body=body,
            sendUpdates="all",
        )
        .execute()
    )

    return created.get("htmlLink")


def build_google_calendar_invite_link(event: Event) -> Optional[str]:
    """
    Builds a Google Calendar "TEMPLATE" link that pre-fills guests (emails).
    This is the best we can do for consumer Gmail without OAuth delegation:
    user opens the link and clicks "Save" to send invitations.
    """
    if not event.guest_emails:
        return None

    emails = [e.strip() for e in (event.guest_emails or "").split(",") if e.strip()]
    if not emails:
        return None

    start_date: date = event.event_date or date.today()
    end_date = start_date + timedelta(days=1)
    dates = f"{start_date.strftime('%Y%m%d')}/{end_date.strftime('%Y%m%d')}"

    details_parts: list[str] = []
    if event.format:
        details_parts.append(f"Формат: {event.format}")
    if event.guests_count is not None:
        details_parts.append(f"Гостей: {event.guests_count}")
    if event.budget is not None:
        details_parts.append(f"Бюджет: {event.budget} ₽")
    if event.notes:
        details_parts.append("")
        details_parts.append(event.notes)

    query = {
        "action": "TEMPLATE",
        "text": event.title,
        "dates": dates,
        "details": "\n".join(details_parts) if details_parts else "",
        "add": ",".join(emails),
        "ctz": settings.GOOGLE_TIMEZONE,
    }
    return "https://calendar.google.com/calendar/render?" + urlencode(query)


def diagnose_calendar_access() -> dict:
    """
    Small helper for debugging integration in runtime.
    Returns basic info and a calendar list sample if available.
    """
    out: dict = {
        "enabled": bool(settings.GOOGLE_CALENDAR_ENABLED),
        "calendar_id": settings.GOOGLE_CALENDAR_ID,
        "service_account_file": settings.GOOGLE_SERVICE_ACCOUNT_FILE,
    }
    service = _get_service()
    if service is None:
        out["service"] = "not_initialized"
        return out

    try:
        cal_list = service.calendarList().list(maxResults=50).execute()
        out["calendar_list_count"] = len(cal_list.get("items", []))
        out["calendar_list_ids"] = [c.get("id") for c in cal_list.get("items", []) if c.get("id")]
    except HttpError as e:
        out["calendar_list_error"] = str(e)
    except Exception as e:
        out["calendar_list_error"] = repr(e)
    return out

