from fastapi import APIRouter, HTTPException, Query

from ..schemas.card import CardSearchResponse, CardSummary
from ..services.cards import card_search_service

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/search", response_model=CardSearchResponse)
def search_cards(q: str = Query(..., min_length=1, max_length=100), limit: int = Query(10, ge=1, le=50)):
    try:
        matches = card_search_service.search(q, limit=limit)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    summaries = [
        CardSummary(name=card.name or "", type_line=card.type_line, oracle_text=card.oracle_text)
        for card in matches
    ]
    return CardSearchResponse(results=summaries)
