from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.event import Event
from app.models.user import User
from app.schemas.recommendation import VenueRecommendationsOut
from app.services.recommendation_service import get_event_recommendations


router = APIRouter(prefix='/events', tags=['recommendations'])


@router.get('/{event_id}/recommendations', response_model=VenueRecommendationsOut)
def event_recommendations(
    event_id: int,
    city: str | None = Query(default=None),
    limit: int = Query(default=6, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = (
        db.query(Event)
        .filter(Event.id == event_id, Event.owner_id == current_user.id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail='Event not found')

    return get_event_recommendations(
        event=event,
        current_user=current_user,
        db=db,
        city_override=city,
        limit=limit,
    )
