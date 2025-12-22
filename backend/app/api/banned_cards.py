"""API endpoints for banned cards."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models.banned_card import BannedCard
from ..schemas.banned_card import (
    BannedCardCreate,
    BannedCardListResponse,
    BannedCardResponse,
    BannedCardUpdate,
)

router = APIRouter(prefix="/banned-cards", tags=["banned-cards"])


@router.get("", response_model=BannedCardListResponse)
def get_banned_cards(
    format: str = Query("Commander", description="Magic format (e.g., Commander, Standard)"),
    db: Session = Depends(get_db),
) -> BannedCardListResponse:
    """Get all banned cards for a specific Magic format."""
    cards = db.query(BannedCard).filter(BannedCard.format == format).all()
    
    return BannedCardListResponse(
        format=format,
        cards=cards,
        count=len(cards),
    )


@router.get("/{card_id}", response_model=BannedCardResponse)
def get_banned_card(
    card_id: int,
    db: Session = Depends(get_db),
) -> BannedCardResponse:
    """Get a specific banned card by ID."""
    card = db.query(BannedCard).filter(BannedCard.id == card_id).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Banned card not found")
    
    return card


@router.get("/search/by-name")
def search_banned_by_name(
    name: str = Query(..., description="Card name to search for"),
    format: Optional[str] = Query(None, description="Filter by format (optional)"),
    db: Session = Depends(get_db),
) -> list[BannedCardResponse]:
    """Search for banned cards by name."""
    query = db.query(BannedCard).filter(BannedCard.card_name.ilike(f"%{name}%"))
    
    if format:
        query = query.filter(BannedCard.format == format)
    
    cards = query.all()
    return cards


@router.post("", response_model=BannedCardResponse)
def create_banned_card(
    banned_card: BannedCardCreate,
    db: Session = Depends(get_db),
) -> BannedCardResponse:
    """Create a new banned card entry."""
    # Check if already exists
    existing = db.query(BannedCard).filter(
        BannedCard.format == banned_card.format,
        BannedCard.card_name == banned_card.card_name,
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Card {banned_card.card_name} is already banned in {banned_card.format}",
        )
    
    db_card = BannedCard(**banned_card.dict())
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    
    return db_card


@router.put("/{card_id}", response_model=BannedCardResponse)
def update_banned_card(
    card_id: int,
    banned_card: BannedCardUpdate,
    db: Session = Depends(get_db),
) -> BannedCardResponse:
    """Update a banned card entry."""
    db_card = db.query(BannedCard).filter(BannedCard.id == card_id).first()
    
    if not db_card:
        raise HTTPException(status_code=404, detail="Banned card not found")
    
    update_data = banned_card.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_card, field, value)
    
    db.commit()
    db.refresh(db_card)
    
    return db_card


@router.delete("/{card_id}")
def delete_banned_card(
    card_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Delete a banned card entry."""
    db_card = db.query(BannedCard).filter(BannedCard.id == card_id).first()
    
    if not db_card:
        raise HTTPException(status_code=404, detail="Banned card not found")
    
    db.delete(db_card)
    db.commit()
    
    return {"status": "deleted", "id": card_id}
