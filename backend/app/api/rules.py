from fastapi import APIRouter, HTTPException
from fastapi.params import Body
from typing import Dict, Any

from ..services import rule_engine

router = APIRouter(prefix="/rules", tags=["rules"])


@router.post("/is_castable")
def api_is_castable(payload: Dict[str, Any] = Body(...)):
    state = payload.get("state", {})
    player_id = payload.get("player_id")
    card_name = payload.get("card_name")
    if not player_id or not card_name:
        raise HTTPException(status_code=400, detail="player_id and card_name required")
    return rule_engine.is_castable(state, player_id, card_name)


@router.post("/validate_targets")
def api_validate_targets(payload: Dict[str, Any] = Body(...)):
    state = payload.get("state", {})
    spell = payload.get("spell", {})
    return rule_engine.validate_targets(state, spell)


@router.post("/resolve_stack")
def api_resolve_stack(payload: Dict[str, Any] = Body(...)):
    state = payload.get("state", {})
    return rule_engine.resolve_stack(state)


@router.post("/compute_combat")
def api_compute_combat(payload: Dict[str, Any] = Body(...)):
    state = payload.get("state", {})
    return rule_engine.compute_combat_damage(state)
