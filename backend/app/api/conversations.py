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
from ..services.melvin import melvin_service
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
    return ConversationDetail(conversation=record, messages=[Message(**msg) for msg in messages])


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
    hits = melvin_service.answer_question(payload.question)
    response_text = format_response(hits)
    await append_message(conversation_id, "melvin", response_text)
    return Message(sender="melvin", content=response_text, created_at=datetime.utcnow())


def format_response(hits: dict) -> str:
    output = []
    if hits.get("rules"):
        output.append("Rules:")
        for rule in hits["rules"]:
            output.append(f"- {rule.get('identifier')}: {rule.get('text')}")
    if hits.get("cards"):
        output.append("Cards:")
        for card in hits["cards"]:
            output.append(f"- {card.get('name')}: {card.get('oracle_text')}")
    if hits.get("rulings"):
        output.append("Rulings:")
        for ruling in hits["rulings"]:
            output.append(f"- {ruling.get('comment')}")
    return "\n".join(output[:100]) or "No relevant information found."
