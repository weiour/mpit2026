from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class InvitationStatus:
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    BOUNCED = "bounced"


class GuestCreate(BaseModel):
    email: str = Field(..., description="Email гостя")
    name: Optional[str] = Field(None, description="Имя гостя")
    phone: Optional[str] = Field(None, description="Телефон гостя")
    # is_birthday_person: bool = Field(False, description="Является ли гость именинником")
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError('Некорректный email адрес')
        return v.lower().strip()


class GuestUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None


class InvitationOut(BaseModel):
    id: int
    event_id: int
    guest_email: str
    guest_name: Optional[str]
    guest_phone: Optional[str]
    # is_birthday_person: bool
    status: str
    token: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    opened_at: Optional[datetime]
    responded_at: Optional[datetime]
    response_notes: Optional[str]
    plus_ones: int
    sent_via: Optional[str]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


class InvitationWithRSVP(InvitationOut):
    attending: Optional[bool] = None
    dietary_restrictions: Optional[str] = None
    music_preferences: Optional[str] = None
    gift_ideas: Optional[str] = None
    questions: Optional[str] = None


class BulkInviteRequest(BaseModel):
    guests: List[GuestCreate] = Field(..., min_items=1, max_items=100, description="Список гостей для приглашения")
    message_template: Optional[str] = Field(None, description="Шаблон сообщения (если не указан - AI сгенерирует)")
    send_via: str = Field("email", description="Канал отправки: email, telegram")
    ai_personalization: bool = Field(True, description="Использовать AI для персонализации сообщений")


class BulkInviteResponse(BaseModel):
    total: int
    created: int
    sent: int
    failed: int
    errors: List[str]
    invitations: List[InvitationOut]


class RSVPResponse(BaseModel):
    token: str
    attending: bool
    notes: Optional[str] = None
    plus_ones: int = Field(0, ge=0, le=10)
    dietary_restrictions: Optional[str] = None
    music_preferences: Optional[str] = None


class RSVPOut(BaseModel):
    id: int
    invitation_id: int
    attending: Optional[bool]
    dietary_restrictions: Optional[str]
    music_preferences: Optional[str]
    gift_ideas: Optional[str]
    questions: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GuestListStats(BaseModel):
    total_guests: int
    pending: int
    sent: int
    delivered: int
    opened: int
    accepted: int
    declined: int
    bounced: int
    attending_count: int
    plus_ones_count: int


class AIInvitationMessage(BaseModel):
    invitation_id: int
    guest_name: str
    guest_email: str
    event_title: str
    event_date: Optional[str]
    event_location: Optional[str]
    personalized_message: str
    subject: str


class PublicWishlistItem(BaseModel):
    """Упрощенная схема вишлиста для публичной страницы"""
    id: int
    title: str
    description: str | None = None
    url: str | None = None
    price: int | None = None
    priority: str | None = None
    # Статус бронирования
    reserved_by_me: bool = False  # Текущий гость забронировал
    reserved_by_other: bool = False  # Другой гость забронировал
    reserved_by_name: str | None = None  # Имя гостя, который забронировал


class PublicInvitation(BaseModel):
    """Схема для публичной страницы приглашения (RSVP)"""
    id: int
    event_title: str
    event_date: Optional[str]
    event_city: Optional[str]
    event_format: Optional[str]
    event_notes: Optional[str]
    guest_email: str
    guest_name: Optional[str]
    # is_birthday_person: bool
    token: str
    status: str
    wishlist: list[PublicWishlistItem] = []
    
    class Config:
        from_attributes = True
