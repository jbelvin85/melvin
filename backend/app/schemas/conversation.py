from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime

    class Config:
        orm_mode = True


class Message(BaseModel):
    sender: str
    content: str
    created_at: datetime
    thinking: Optional[List["ThinkingStep"]] = None


class MessageCreate(BaseModel):
    question: str = Field(..., min_length=3)
    tone: str | None = None
    detail_level: str | None = None
    card_names: List[str] | None = None


class ConversationDetail(BaseModel):
    conversation: ConversationOut
    messages: List[Message]


class ThinkingStep(BaseModel):
    label: str
    detail: str


Message.model_rebuild()
