from fastapi import APIRouter

from . import auth, banned_cards, conversations


router = APIRouter()


@router.get("/health", tags=["system"])
def healthcheck() -> dict:
    return {"status": "ok"}


router.include_router(auth.router)
router.include_router(banned_cards.router)
router.include_router(conversations.router)


