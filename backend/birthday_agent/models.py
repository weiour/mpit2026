from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    user_id: str = "local_user"
    name: Optional[str] = None
    birthday_date: Optional[date] = None
    city: Optional[str] = None
    budget_rub: Optional[int] = Field(default=None, ge=0)
    guests_count: Optional[int] = Field(default=None, ge=0)
    format: Optional[Literal["home", "restaurant", "outdoor", "mixed"]] = None
    vibe_keywords: list[str] = Field(default_factory=list)
    dietary_restrictions: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)
    must_haves: list[str] = Field(default_factory=list)
    contacts_note: Optional[str] = None


class TaskItem(BaseModel):
    id: str
    title: str
    description: str = ""
    due_at: Optional[datetime] = None
    status: Literal["todo", "in_progress", "done", "blocked"] = "todo"
    owner: Literal["agent", "user"] = "agent"
    priority: Literal["low", "medium", "high"] = "medium"


class PlanDraft(BaseModel):
    concept_title: str
    concept_summary: str
    venue_ideas: list[str] = Field(default_factory=list)
    menu_ideas: list[str] = Field(default_factory=list)
    gift_ideas: list[str] = Field(default_factory=list)
    entertainment_ideas: list[str] = Field(default_factory=list)
    decor_ideas: list[str] = Field(default_factory=list)
    invitation_text: str
    checklist: list[TaskItem] = Field(default_factory=list)

