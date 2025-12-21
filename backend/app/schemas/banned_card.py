"""Pydantic schemas for banned card endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BannedCardCreate(BaseModel):
    """Schema for creating a banned card entry."""

    format: str
    card_name: str
    reason: Optional[str] = None
    ban_date: Optional[datetime] = None


class BannedCardUpdate(BaseModel):
    """Schema for updating a banned card entry."""

    format: Optional[str] = None
    card_name: Optional[str] = None
    reason: Optional[str] = None
    ban_date: Optional[datetime] = None


class BannedCardResponse(BaseModel):
    """Schema for returning banned card information."""

    id: int
    format: str
    card_name: str
    reason: Optional[str] = None
    ban_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BannedCardListResponse(BaseModel):
    """Schema for returning a list of banned cards for a format."""

    format: str
    cards: list[BannedCardResponse]
    count: int
