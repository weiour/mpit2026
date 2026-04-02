from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class WishlistReservation(Base):
    """Модель для бронирования подарков гостями"""
    __tablename__ = "wishlist_reservations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Связь с элементом вишлиста
    wishlist_item_id = Column(Integer, ForeignKey("wishlists.id"), nullable=False)
    
    # Связь с приглашением (гостем)
    invitation_id = Column(Integer, ForeignKey("invitations.id"), nullable=False)
    
    # Дополнительная информация
    guest_name = Column(String, nullable=True)  # Имя гостя для отображения
    notes = Column(Text, nullable=True)  # Примечания гостя
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Отношения
    wishlist_item = relationship("Wishlist", back_populates="reservations")
    invitation = relationship("Invitation", back_populates="wishlist_reservations")
