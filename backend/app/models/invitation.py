from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class InvitationStatus(str, enum.Enum):
    PENDING = "pending"      # Приглашение создано, но не отправлено
    SENT = "sent"            # Приглашение отправлено
    DELIVERED = "delivered"  # Приглашение доставлено
    OPENED = "opened"        # Гость открыл приглашение
    ACCEPTED = "accepted"    # Гость принял приглашение
    DECLINED = "declined"    # Гость отклонил приглашение
    BOUNCED = "bounced"      # Email не существует или недоступен


class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    
    # Информация о госте
    guest_email = Column(String, nullable=False)
    guest_name = Column(String, nullable=True)
    guest_phone = Column(String, nullable=True)
    # is_birthday_person = Column(Boolean, default=False)  # REMOVED - колонки нет в БД
    
    # Статус приглашения
    status = Column(String, default=InvitationStatus.PENDING.value)
    
    # Токен для уникальной ссылки приглашения
    token = Column(String, unique=True, index=True)
    
    # Даты
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    
    # Ответ гостя
    response_notes = Column(Text, nullable=True)  # Комментарий гостя
    plus_ones = Column(Integer, default=0)  # Количество дополнительных гостей
    
    # Информация об отправке
    sent_via = Column(String, nullable=True)  # email, telegram, etc.
    message_content = Column(Text, nullable=True)  # Содержимое отправленного сообщения
    error_message = Column(String, nullable=True)  # Ошибка если отправка не удалась
    
    # AI-агент
    ai_agent_id = Column(String, nullable=True)  # ID сессии AI агента
    ai_conversation = Column(Text, nullable=True)  # История диалога с гостем

    event = relationship("Event", back_populates="invitations")
    rsvp = relationship("GuestRSVP", back_populates="invitation", uselist=False, cascade="all, delete-orphan", single_parent=True)
    wishlist_reservations = relationship("WishlistReservation", back_populates="invitation", cascade="all, delete-orphan")


class GuestRSVP(Base):
    __tablename__ = "guest_rsvps"
    
    id = Column(Integer, primary_key=True, index=True)
    invitation_id = Column(Integer, ForeignKey("invitations.id"), nullable=False, unique=True)
    
    # Детали ответа
    attending = Column(Boolean, nullable=True)  # True = идет, False = не идет, None = не ответил
    dietary_restrictions = Column(Text, nullable=True)  # Особенности питания
    music_preferences = Column(Text, nullable=True)  # Музыкальные предпочтения
    gift_ideas = Column(Text, nullable=True)  # Идеи подарков
    questions = Column(Text, nullable=True)  # Вопросы гостю
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    invitation = relationship("Invitation", back_populates="rsvp")
