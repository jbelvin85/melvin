from fastapi import APIRouter, HTTPException, Body, Depends, Request
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional

from ..dependencies import get_db
from ..services.melvin import get_melvin_service
from ..services import rule_engine
from ..services.state_manager import state_manager_cls

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/analyze")
def analyze(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Run deterministic tools on a board state and ask Melvin to analyze.

    payload may include either `state_id` or a full `state` object, and a `question` string.
    Returns deterministic tool outputs plus the LLM answer.
    """
    state = None
    if "state_id" in payload:
        # Use StateManager to fetch
        manager = state_manager_cls(db)
        rec = manager.get_state(payload.get("state_id"))
        if not rec:
            raise HTTPException(status_code=404, detail="State not found")
        state = rec.state
    else:
        state = payload.get("state")

    if not state:
        raise HTTPException(status_code=400, detail="No state provided")

    question = payload.get("question")
    if not question:
        raise HTTPException(status_code=400, detail="No question provided")

    tools_outputs: Dict[str, Any] = {}

    # Run simple deterministic analyses
    try:
        # Check castability for battlefield permanents for the first player (if exists)
        players = state.get("players", [])
        player_id = players[0].get("id") if players else None
        battlefield = state.get("battlefield", [])
        cast_checks = {}
        for obj in battlefield:
            name = obj.get("card_name")
            if not name or not player_id:
                continue
            cast_checks[name] = rule_engine.is_castable(state, player_id, name)
        tools_outputs["cast_checks"] = cast_checks

        # Validate targets for spells on stack
        stack = state.get("stack", [])
        stack_validations = []
        for spell in stack:
            stack_validations.append({"spell": spell.get("card_name"), "validation": rule_engine.validate_targets(state, spell)})
        tools_outputs["stack_validations"] = stack_validations

        # Simulate resolving top of stack
        tools_outputs["resolve_preview"] = rule_engine.resolve_stack(state)

        # Compute combat preview if attackers present
        if state.get("attackers"):
            tools_outputs["combat_preview"] = rule_engine.compute_combat_damage(state)
    except Exception as e:
        tools_outputs["tool_error"] = str(e)

    # Compose tools_context and call Melvin
    tools_context_parts = []
    for k, v in tools_outputs.items():
        tools_context_parts.append(f"{k}: {v}")

    try:
        answer = get_melvin_service().answer_question(question)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    return {"tools": tools_outputs, "answer": answer}
