from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models.conversation import Conversation
from ..models.user import User
from ..schemas.conversation import (
    ConversationCreate,
    ConversationDetail,
    ConversationOut,
    Message,
    MessageCreate,
)
from ..services.melvin import get_melvin_service
from ..services.messages import append_message, fetch_messages


router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/", response_model=list[ConversationOut])
def list_conversations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ConversationOut]:
    records = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )
    return records


@router.post("/", response_model=ConversationOut)
def create_conversation(
    payload: ConversationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationOut:
    record = Conversation(user_id=user.id, title=payload.title)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationDetail:
    record = db.get(Conversation, conversation_id)
    if not record or record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = await fetch_messages(conversation_id)
    from ..schemas.conversation import ConversationOut

    conversation_schema = ConversationOut.model_validate(record)
    return ConversationDetail(conversation=conversation_schema, messages=[Message(**msg) for msg in messages])


@router.post("/{conversation_id}/chat", response_model=Message)
async def chat_with_melvin(
    conversation_id: int,
    payload: MessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Message:
    record = db.get(Conversation, conversation_id)
    if not record or record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await append_message(conversation_id, "user", payload.question)
    response_text, thinking_steps = get_melvin_service().answer_question_with_details(payload.question, user=user)
    await append_message(conversation_id, "melvin", response_text, thinking=thinking_steps)
    return Message(sender="melvin", content=response_text, created_at=datetime.utcnow(), thinking=thinking_steps)
