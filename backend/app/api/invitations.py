from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import secrets
import string

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models import User, Event, Invitation, GuestRSVP
from app.schemas.invitation import (
    GuestCreate, GuestUpdate, InvitationOut, InvitationWithRSVP,
    BulkInviteRequest, BulkInviteResponse, RSVPResponse, RSVPOut,
    GuestListStats, AIInvitationMessage, PublicInvitation
)
from app.services.invitation_service import InvitationService

# Основной роутер для управления приглашениями (требует авторизации)
router = APIRouter(prefix="/events/{event_id}/invitations", tags=["invitations"])

# Публичный роутер для гостей (без авторизации)
public_router = APIRouter(prefix="/invitations", tags=["public-invitations"])


def generate_token():
    """Генерация уникального токена для приглашения"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))


@router.get("", response_model=List[InvitationWithRSVP])
def list_invitations(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить список всех приглашений для события"""
    event = db.query(Event).filter(Event.id == event_id, Event.owner_id == current_user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    
    invitations = db.query(Invitation).filter(Invitation.event_id == event_id).all()
    
    result = []
    for inv in invitations:
        inv_data = InvitationOut.from_orm(inv)
        rsvp = db.query(GuestRSVP).filter(GuestRSVP.invitation_id == inv.id).first()
        
        data = inv_data.dict()
        if rsvp:
            data.update({
                'attending': rsvp.attending,
                'dietary_restrictions': rsvp.dietary_restrictions,
                'music_preferences': rsvp.music_preferences,
                'gift_ideas': rsvp.gift_ideas,
                'questions': rsvp.questions
            })
        result.append(InvitationWithRSVP(**data))
    
    return result


@router.post("/bulk", response_model=BulkInviteResponse)
def create_bulk_invitations(
    event_id: int,
    request: BulkInviteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создать и отправить приглашения группе гостей через AI-агента"""
    event = db.query(Event).filter(Event.id == event_id, Event.owner_id == current_user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    
    invitation_service = InvitationService(db)
    result = invitation_service.create_and_send_invitations(
        event=event,
        guests=request.guests,
        message_template=request.message_template,
        send_via=request.send_via,
        ai_personalization=request.ai_personalization,
        background_tasks=background_tasks
    )
    
    return result


@router.post("/{invitation_id}/resend")
def resend_invitation(
    event_id: int,
    invitation_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Повторно отправить приглашение конкретному гостю"""
    event = db.query(Event).filter(Event.id == event_id, Event.owner_id == current_user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    
    invitation = db.query(Invitation).filter(
        Invitation.id == invitation_id,
        Invitation.event_id == event_id
    ).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Приглашение не найдено")
    
    invitation_service = InvitationService(db)
    success = invitation_service.resend_invitation(invitation, background_tasks)
    
    if success:
        return {"message": "Приглашение отправлено", "status": "sent"}
    else:
        raise HTTPException(status_code=500, detail="Не удалось отправить приглашение")


@router.delete("/{invitation_id}")
def delete_invitation(
    event_id: int,
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удалить приглашение"""
    event = db.query(Event).filter(Event.id == event_id, Event.owner_id == current_user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    
    invitation = db.query(Invitation).filter(
        Invitation.id == invitation_id,
        Invitation.event_id == event_id
    ).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Приглашение не найдено")
    
    db.delete(invitation)
    db.commit()
    
    return {"message": "Приглашение удалено"}


@router.get("/stats", response_model=GuestListStats)
def get_invitation_stats(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить статистику по приглашениям"""
    event = db.query(Event).filter(Event.id == event_id, Event.owner_id == current_user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    
    invitations = db.query(Invitation).filter(Invitation.event_id == event_id).all()
    
    stats = {
        'total_guests': len(invitations),
        'pending': sum(1 for i in invitations if i.status == 'pending'),
        'sent': sum(1 for i in invitations if i.status == 'sent'),
        'delivered': sum(1 for i in invitations if i.status == 'delivered'),
        'opened': sum(1 for i in invitations if i.status == 'opened'),
        'accepted': sum(1 for i in invitations if i.status == 'accepted'),
        'declined': sum(1 for i in invitations if i.status == 'declined'),
        'bounced': sum(1 for i in invitations if i.status == 'bounced'),
        'attending_count': sum(1 for i in invitations if i.status == 'accepted'),
        'plus_ones_count': sum(i.plus_ones for i in invitations if i.status == 'accepted')
    }
    
    return GuestListStats(**stats)


# Публичные endpoints для гостей (не требуют авторизации)

@router.post("/rsvp/{token}", response_model=RSVPOut)
def submit_rsvp(
    token: str,
    response: RSVPResponse,
    db: Session = Depends(get_db)
):
    """Гость подтверждает или отклоняет приглашение"""
    if token != response.token:
        raise HTTPException(status_code=400, detail="Некорректный токен")
    
    invitation = db.query(Invitation).filter(Invitation.token == token).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Приглашение не найдено")
    
    # Обновляем статус приглашения
    invitation.status = 'accepted' if response.attending else 'declined'
    invitation.response_notes = response.notes
    invitation.plus_ones = response.plus_ones
    
    # Создаем или обновляем RSVP
    rsvp = db.query(GuestRSVP).filter(GuestRSVP.invitation_id == invitation.id).first()
    if not rsvp:
        rsvp = GuestRSVP(invitation_id=invitation.id)
        db.add(rsvp)
    
    rsvp.attending = response.attending
    rsvp.dietary_restrictions = response.dietary_restrictions
    rsvp.music_preferences = response.music_preferences
    
    db.commit()
    db.refresh(rsvp)
    
    return RSVPOut.from_orm(rsvp)


@router.get("/public/{token}", response_model=InvitationOut)
def get_public_invitation(
    token: str,
    db: Session = Depends(get_db)
):
    """Публичная страница приглашения (для гостя по ссылке)"""
    invitation = db.query(Invitation).filter(Invitation.token == token).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Приглашение не найдено")
    
    # Обновляем статус на "opened" если еще не открыто
    if not invitation.opened_at:
        from datetime import datetime
        invitation.opened_at = datetime.utcnow()
        if invitation.status in ['sent', 'delivered']:
            invitation.status = 'opened'
        db.commit()
    
    return InvitationOut.from_orm(invitation)


# Публичные endpoints для гостей (без авторизации, вне основного роутера)

@public_router.get("/rsvp/{token}", response_model=PublicInvitation)
def get_invitation_by_token(token: str, db: Session = Depends(get_db)):
    """Получить информацию о приглашении по токену (для страницы RSVP)"""
    invitation = db.query(Invitation).filter(Invitation.token == token).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Приглашение не найдено")
    
    event = db.query(Event).filter(Event.id == invitation.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    
    # Обновляем статус на "opened"
    if not invitation.opened_at:
        from datetime import datetime
        invitation.opened_at = datetime.utcnow()
        if invitation.status in ['sent', 'delivered']:
            invitation.status = 'opened'
        db.commit()
    
    return PublicInvitation(
        id=invitation.id,
        event_title=event.title,
        event_date=str(event.event_date) if event.event_date else None,
        event_city=event.city,
        event_format=event.format,
        event_notes=event.notes,
        guest_email=invitation.guest_email,
        guest_name=invitation.guest_name,
        token=invitation.token,
        status=invitation.status
    )


@public_router.post("/rsvp/{token}", response_model=RSVPOut)
def submit_rsvp_public(
    token: str,
    response: RSVPResponse,
    db: Session = Depends(get_db)
):
    """Гость подтверждает или отклоняет приглашение (публичный endpoint)"""
    if token != response.token:
        raise HTTPException(status_code=400, detail="Некорректный токен")
    
    invitation = db.query(Invitation).filter(Invitation.token == token).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Приглашение не найдено")
    
    # Обновляем статус приглашения
    invitation.status = 'accepted' if response.attending else 'declined'
    invitation.response_notes = response.notes
    invitation.plus_ones = response.plus_ones
    from datetime import datetime
    invitation.responded_at = datetime.utcnow()
    
    # Создаем или обновляем RSVP
    rsvp = db.query(GuestRSVP).filter(GuestRSVP.invitation_id == invitation.id).first()
    if not rsvp:
        rsvp = GuestRSVP(invitation_id=invitation.id)
        db.add(rsvp)
    
    rsvp.attending = response.attending
    rsvp.dietary_restrictions = response.dietary_restrictions
    rsvp.music_preferences = response.music_preferences
    rsvp.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(rsvp)
    
    return RSVPOut.from_orm(rsvp)
