"""Model for tracking banned Magic cards by format."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text

from ..core.database import Base


class BannedCard(Base):
    """Represents a banned card in a specific Magic format."""

    __tablename__ = "banned_cards"

    id = Column(Integer, primary_key=True, index=True)
    format = Column(String(64), nullable=False, index=True)  # e.g., "Commander", "Standard"
    card_name = Column(String(255), nullable=False, index=True)
    reason = Column(Text, nullable=True)
    ban_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<BannedCard(format={self.format}, card_name={self.card_name})>"
