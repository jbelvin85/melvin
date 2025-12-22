"""Service to manage game board states."""

from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session

from ..models.game_state import GameState
from ..core.database import SessionLocal


class StateManager:
    """Simple CRUD wrapper around GameState model.

    The `state` JSON should follow a minimal schema:
    {
      "players": [{"name": "Alice", "life": 40, "id": "p1"}, ...],
      "battlefield": [{"id": "c1", "card_name": "Sol Ring", "controller": "p1", "tapped": false, "zone_id": "bf1"}],
      "stack": [],
      "turn": {"active_player": "p1", "step": "precombat_main"}
    }
    """

    def __init__(self, db: Session):
        self.db = db

    @classmethod
    def create_from_local(cls):
        return cls(SessionLocal())

    def create_state(self, name: str, owner: Optional[str], state: dict) -> GameState:
        record = GameState(name=name, owner=owner, state=state)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_state(self, state_id: int) -> Optional[GameState]:
        return self.db.get(GameState, state_id)

    def list_states(self) -> list[GameState]:
        return self.db.query(GameState).order_by(GameState.updated_at.desc()).all()

    def update_state(self, state_id: int, state: dict) -> Optional[GameState]:
        record = self.db.get(GameState, state_id)
        if not record:
            return None
        record.state = state
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def delete_state(self, state_id: int) -> bool:
        record = self.db.get(GameState, state_id)
        if not record:
            return False
        self.db.delete(record)
        self.db.commit()
        return True


state_manager_cls = StateManager
