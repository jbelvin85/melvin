"""Service for managing banned cards data."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..models.banned_card import BannedCard


class BannedCardsService:
    """Service for loading and managing banned cards data."""

    def __init__(self):
        settings = get_settings()
        self.banned_cards_path = settings.raw_data_dir / "banned-cards-commander.json"

    def load_from_json(self, db: Session, path: Optional[Path] = None) -> int:
        """
        Load banned cards from a JSON file and populate the database.
        
        Returns the number of cards loaded.
        """
        if path is None:
            path = self.banned_cards_path
        
        if not path.exists():
            print(f"Banned cards file not found at {path}")
            return 0
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading banned cards file: {e}")
            return 0
        
        format_name = data.get("format", "Commander")
        banned_cards = data.get("banned_cards", [])
        
        count = 0
        for card_data in banned_cards:
            card_name = card_data.get("name")
            if not card_name:
                continue
            
            # Check if card already exists
            existing = db.query(BannedCard).filter(
                BannedCard.format == format_name,
                BannedCard.card_name == card_name,
            ).first()
            
            if not existing:
                ban_date = card_data.get("ban_date")
                if ban_date and isinstance(ban_date, str):
                    ban_date = datetime.fromisoformat(ban_date)
                
                db_card = BannedCard(
                    format=format_name,
                    card_name=card_name,
                    reason=card_data.get("reason"),
                    ban_date=ban_date,
                )
                db.add(db_card)
                count += 1
        
        db.commit()
        return count

    def get_banned_cards(self, db: Session, format_name: str = "Commander") -> list[BannedCard]:
        """Get all banned cards for a specific format."""
        return db.query(BannedCard).filter(BannedCard.format == format_name).all()

    def is_card_banned(
        self, db: Session, card_name: str, format_name: str = "Commander"
    ) -> bool:
        """Check if a specific card is banned in a format."""
        card = db.query(BannedCard).filter(
            BannedCard.format == format_name,
            BannedCard.card_name == card_name,
        ).first()
        return card is not None


# Singleton instance
banned_cards_service = BannedCardsService()
