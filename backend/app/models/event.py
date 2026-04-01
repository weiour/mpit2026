from sqlalchemy import Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    event_date = Column(Date, nullable=True)
    budget = Column(Integer, nullable=True)
    guests_count = Column(Integer, nullable=True)
    format = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    status = Column(String, nullable=True, default="draft")
    venue_mode = Column(String, nullable=True)
    selected_option = Column(Text, nullable=True)
    selected_option_kind = Column(String, nullable=True)
    google_calendar_link = Column(Text, nullable=True)
    google_calendar_error = Column(Text, nullable=True)
    guest_emails = Column(Text, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="events")
    messages = relationship("ChatMessage", back_populates="event", cascade="all, delete-orphan")
    wishlist_items = relationship("Wishlist", back_populates="event", cascade="all, delete-orphan")
    invitations = relationship("Invitation", back_populates="event", cascade="all, delete-orphan")
