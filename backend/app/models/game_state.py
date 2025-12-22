from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, DateTime
from ..core.database import Base


class GameState(Base):
    __tablename__ = "game_states"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=True)
    # canonical representation of the board: players, zones, permanents, stack
    state = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "owner": self.owner,
            "state": self.state,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
