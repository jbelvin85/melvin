from fastapi import APIRouter

from . import auth, conversations
from ..schemas.chat import ChatRequest, ChatResponse
from ..services.melvin import melvin_service


router = APIRouter()


@router.get("/health", tags=["system"])
def healthcheck() -> dict:
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    hits = melvin_service.answer_question(payload.question)
    return ChatResponse(**hits)


router.include_router(auth.router)
router.include_router(conversations.router)
