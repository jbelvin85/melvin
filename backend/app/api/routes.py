from fastapi import APIRouter

from . import auth, banned_cards, conversations, profiles, scryfall, game_state, rules, cards


router = APIRouter()


@router.get("/health", tags=["system"])
def healthcheck() -> dict:
    return {"status": "ok"}


router.include_router(auth.router)
router.include_router(banned_cards.router)
router.include_router(conversations.router)
router.include_router(profiles.router)
router.include_router(scryfall.router)
router.include_router(game_state.router)
router.include_router(rules.router)
router.include_router(cards.router)

