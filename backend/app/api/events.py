from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.event import Event
from app.models.user import User
from app.schemas.event import EventCreate, EventOut, EventUpdate
from app.services.google_calendar import (
    build_google_calendar_invite_link,
    create_calendar_event_for_event,
    diagnose_calendar_access,
)


router = APIRouter(prefix="/events", tags=["events"])


def _attach_google_links(event: Event):
    try:
        setattr(event, "google_invite_link", build_google_calendar_invite_link(event))
    except Exception:
        setattr(event, "google_invite_link", None)
    return event


@router.post("", response_model=EventOut)
def create_event(
    data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = Event(
        title=data.title,
        event_date=data.event_date,
        budget=data.budget,
        guests_count=data.guests_count,
        format=data.format,
        notes=data.notes,
        city=data.city,
        status=data.status or "draft",
        venue_mode=data.venue_mode,
        selected_option=data.selected_option,
        selected_option_kind=data.selected_option_kind,
        guest_emails=",".join(data.guest_emails) if data.guest_emails else None,
        owner_id=current_user.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    event = _attach_google_links(event)

    try:
        link = create_calendar_event_for_event(event, current_user)
        event.google_calendar_link = link
        event.google_calendar_error = None
    except Exception as e:
        event.google_calendar_link = None
        event.google_calendar_error = str(e)

    db.add(event)
    db.commit()
    db.refresh(event)

    return _attach_google_links(event)


@router.get("/google-calendar/diagnose")
def google_calendar_diagnose(current_user: User = Depends(get_current_user)):
    return diagnose_calendar_access()


@router.get("", response_model=list[EventOut])
def list_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = db.query(Event).filter(Event.owner_id == current_user.id).order_by(Event.id.desc()).all()
    return [_attach_google_links(ev) for ev in items]


@router.get("/{event_id}", response_model=EventOut)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.query(Event).filter(Event.id == event_id, Event.owner_id == current_user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return _attach_google_links(event)


@router.patch("/{event_id}", response_model=EventOut)
def update_event(
    event_id: int,
    data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.query(Event).filter(Event.id == event_id, Event.owner_id == current_user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    payload = data.model_dump(exclude_unset=True)
    if "guest_emails" in payload:
        event.guest_emails = ",".join(payload.pop("guest_emails") or []) or None

    for key, value in payload.items():
        setattr(event, key, value)

    db.add(event)
    db.commit()
    db.refresh(event)
    return _attach_google_links(event)
