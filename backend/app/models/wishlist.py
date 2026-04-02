from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Wishlist(Base):
    __tablename__ = "wishlists"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    price = Column(Integer, nullable=True)
    priority = Column(String, nullable=True, default="medium")
    status = Column(String, nullable=True, default="active")

    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    event = relationship("Event", back_populates="wishlist_items")
    reservations = relationship("WishlistReservation", back_populates="wishlist_item", cascade="all, delete-orphan")
