from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatAskIn(BaseModel):
    message: str


class ChatActionOut(BaseModel):
    id: str
    label: str
    kind: Literal["send_prompt", "open_tab"] = "send_prompt"
    prompt: str | None = None
    target_tab: str | None = None


class ChatMessageOut(BaseModel):
    id: int
    event_id: int
    role: str
    content: str
    created_at: datetime | None
    actions: list[ChatActionOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ChatResponseOut(BaseModel):
    user_message: ChatMessageOut
    assistant_message: ChatMessageOut
