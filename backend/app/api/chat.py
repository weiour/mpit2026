from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.chat import ChatMessage
from app.models.event import Event
from app.models.user import User
from app.schemas.chat import ChatAskIn, ChatMessageOut, ChatResponseOut
from app.services.chat_service import ask_gigachat, serialize_chat_message


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/events/{event_id}", response_model=ChatResponseOut)
def send_message(
    event_id: int,
    data: ChatAskIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = (
        db.query(Event)
        .filter(Event.id == event_id, Event.owner_id == current_user.id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    user_msg, assistant_msg = ask_gigachat(event, data.message, db)

    return ChatResponseOut(
        user_message=serialize_chat_message(user_msg, event),
        assistant_message=serialize_chat_message(assistant_msg, event),
    )


@router.get("/events/{event_id}", response_model=list[ChatMessageOut])
def get_chat_history(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = (
        db.query(Event)
        .filter(Event.id == event_id, Event.owner_id == current_user.id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.event_id == event_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    return [serialize_chat_message(message, event) for message in history]
