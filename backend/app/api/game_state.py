from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from ..dependencies import get_db, get_current_user
from ..services.state_manager import StateManager, state_manager_cls

router = APIRouter(prefix="/game_state", tags=["game_state"])


@router.post("/", status_code=201)
def create_state(payload: dict, db: Session = Depends(get_db)) -> dict:
    manager = state_manager_cls(db)
    name = payload.get("name", "Untitled")
    owner = payload.get("owner")
    state = payload.get("state", {})
    rec = manager.create_state(name, owner, state)
    return rec.to_dict()


@router.get("/")
def list_states(db: Session = Depends(get_db)) -> list[dict]:
    manager = state_manager_cls(db)
    recs = manager.list_states()
    return [r.to_dict() for r in recs]


@router.get("/{state_id}")
def get_state(state_id: int, db: Session = Depends(get_db)) -> dict:
    manager = state_manager_cls(db)
    rec = manager.get_state(state_id)
    if not rec:
        raise HTTPException(status_code=404, detail="State not found")
    return rec.to_dict()


@router.put("/{state_id}")
def update_state(state_id: int, payload: dict, db: Session = Depends(get_db)) -> dict:
    manager = state_manager_cls(db)
    state = payload.get("state")
    if state is None:
        raise HTTPException(status_code=400, detail="Missing state payload")
    rec = manager.update_state(state_id, state)
    if not rec:
        raise HTTPException(status_code=404, detail="State not found")
    return rec.to_dict()


@router.delete("/{state_id}")
def delete_state(state_id: int, db: Session = Depends(get_db)) -> dict:
    manager = state_manager_cls(db)
    ok = manager.delete_state(state_id)
    if not ok:
        raise HTTPException(status_code=404, detail="State not found")
    return {"deleted": True}
