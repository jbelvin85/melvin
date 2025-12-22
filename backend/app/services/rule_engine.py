"""Enhanced deterministic rule engine helpers.

This module improves on the starter implementation by parsing mana costs,
checking colored and generic mana payment against a player's mana pool or
available total, and applying basic timing rules for casting (instant vs
sorcery speed). The functions remain conservative and return `unknown` when
insufficient data is present.

This is not a full rules engine — it is a pragmatic toolset to make the
assistant's behavior auditable and less reliant on LLM hallucinations.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Tuple
from ..services.scryfall import scryfall_service

# ensure logs directory exists
os.makedirs(os.path.join(os.path.dirname(__file__), "..", "..", "logs"), exist_ok=True)
logger = logging.getLogger("rule_engine")
if not logger.handlers:
    fh = logging.FileHandler(os.path.join(os.path.dirname(__file__), "..", "..", "logs", "rule_engine.log"))
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)


MANA_COLORS = ["W", "U", "B", "R", "G"]


def parse_mana_cost(mana_cost: str) -> Dict[str, Any]:
    """Parse a Scryfall-style mana_cost like "{2}{U}{U}" into a structure.

    Returns dict with keys: `cmc`, `generic`, `colored` (dict), `symbols` (list)
    """
    if not mana_cost:
        return {"cmc": 0, "generic": 0, "colored": {}, "symbols": []}
    tokens = re.findall(r"\{([^}]+)\}", mana_cost)
    generic = 0
    colored: Dict[str, int] = {c: 0 for c in MANA_COLORS}
    symbols: List[str] = []
    cmc = 0
    for t in tokens:
        symbols.append(t)
        # numeric generic cost
        if t.isdigit():
            val = int(t)
            generic += val
            cmc += val
            continue
        # X cost
        if t.upper() == "X":
            cmc += 0  # unknown until X is chosen
            continue
        # single color symbol
        if t in MANA_COLORS:
            colored[t] += 1
            cmc += 1
            continue
        # hybrid or phyrexian symbol contains '/'
        if "/" in t:
            # treat hybrid as 1 cmc; color requirement is flexible — count as generic for now
            cmc += 1
            generic += 1
            continue
        # otherwise, count as 1 cmc
        cmc += 1

    return {"cmc": cmc, "generic": generic, "colored": colored, "symbols": symbols}


def _fetch_card(card_name: str) -> Dict[str, Any] | None:
    try:
        return scryfall_service.get_card(f"named?fuzzy={card_name}")
    except Exception:
        return None


def _sum_mana_pool(mana_pool: Dict[str, int]) -> int:
    return sum(mana_pool.get(c, 0) for c in list(mana_pool.keys()))


def can_pay_cost(parsed_cost: Dict[str, Any], player: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Check whether `player` can pay `parsed_cost` given `player` has either
    `mana_pool` (dict of color counts) or `mana_available` (total generic).

    Returns (payable, details)
    """
    mana_pool = player.get("mana_pool")
    mana_available = player.get("mana_available")

    # If a mana pool mapping provided, respect colored requirements
    if mana_pool:
        # check colored
        for c, needed in parsed_cost.get("colored", {}).items():
            if needed and mana_pool.get(c, 0) < needed:
                return False, {"reason": "missing_colored", "color": c}
        # check generic: sum remaining mana after paying colored
        remaining = _sum_mana_pool(mana_pool) - sum(parsed_cost.get("colored", {}).values())
        if remaining >= parsed_cost.get("generic", 0):
            return True, {"reason": None}
        return False, {"reason": "insufficient_generic", "needed": parsed_cost.get("generic", 0), "available": remaining}

    # Fallback to numeric mana_available
    if mana_available is not None:
        if mana_available >= parsed_cost.get("cmc", 0):
            return True, {"reason": None}
        return False, {"reason": "insufficient_mana", "needed": parsed_cost.get("cmc", 0), "available": mana_available}

    return False, {"reason": "missing_mana_info"}


def is_castable(state: Dict[str, Any], player_id: str, card_name: str) -> Dict[str, Any]:
    """Determine whether the player can cast `card_name` given `state`.

    Checks: card existence, mana cost payment, and basic timing (instant vs sorcery).
    Returns a dict with `castable` (True/False/'unknown') and `reason`.
    """
    card = _fetch_card(card_name)
    if not card:
        return {"castable": False, "reason": "card_not_found"}

    mana_cost = card.get("mana_cost") or ""
    parsed = parse_mana_cost(mana_cost)

    players = state.get("players", [])
    player = next((p for p in players if p.get("id") == player_id or p.get("name") == player_id), None)
    if not player:
        res = {"castable": False, "reason": "player_not_found"}
        logger.info({"action": "is_castable", "player_id": player_id, "card_name": card_name, "result": res})
        return res

    # check mana payment
    payable, details = can_pay_cost(parsed, player)
    if not payable:
        res = {"castable": False, "reason": details.get("reason"), **details}
        logger.info({"action": "is_castable", "player_id": player_id, "card_name": card_name, "result": res})
        return res

    # timing rules
    type_line = (card.get("type_line") or "").lower()
    oracle = (card.get("oracle_text") or "").lower()

    # instant or has flash
    if "instant" in type_line or "flash" in oracle or "flash" in type_line:
        res = {"castable": True, "reason": None}
        logger.info({"action": "is_castable", "player_id": player_id, "card_name": card_name, "result": res})
        return res

    # sorcery-speed checks: must be active player's main phase with empty stack
    turn = state.get("turn", {})
    active = turn.get("active_player")
    phase = (turn.get("step") or "").lower()
    stack = state.get("stack", [])

    # if player is not the active player and no flash, can't cast non-instant
    if active != player.get("id") and active != player.get("name"):
        res = {"castable": False, "reason": "not_active_player"}
        logger.info({"action": "is_castable", "player_id": player_id, "card_name": card_name, "result": res})
        return res

    # require main phase (precombat_main or postcombat_main) and empty stack
    if phase not in ("precombat_main", "postcombat_main", "main"):
        res = {"castable": False, "reason": "not_main_phase", "phase": phase}
        logger.info({"action": "is_castable", "player_id": player_id, "card_name": card_name, "result": res})
        return res

    if stack:
        res = {"castable": False, "reason": "stack_not_empty"}
        logger.info({"action": "is_castable", "player_id": player_id, "card_name": card_name, "result": res})
        return res

    res = {"castable": True, "reason": None}
    logger.info({"action": "is_castable", "player_id": player_id, "card_name": card_name, "result": res})
    return res


def validate_targets(state: Dict[str, Any], spell: Dict[str, Any]) -> Dict[str, Any]:
    """Validate existence and simple legality of declared targets.

    Uses battlefield presence and naive oracle-text checks for "target creature" etc.
    """
    targets = spell.get("targets", []) or []
    battlefield = state.get("battlefield", [])
    problems: List[str] = []

    # if card requires a target according to oracle text, ensure targets provided
    card_name = spell.get("card_name")
    card = _fetch_card(card_name) if card_name else None
    oracle = (card.get("oracle_text") if card else spell.get("oracle_text", "")) or ""
    requires_target = "target" in oracle.lower()
    if requires_target and not targets:
        problems.append("missing_required_target")

    for t in targets:
        if t.get("id"):
            found = any(obj.get("id") == t.get("id") for obj in battlefield)
            if not found:
                problems.append(f"target_not_found:{t.get('id')}")
        elif t.get("filter"):
            f = t.get("filter").lower()
            found = any(f in (obj.get("card_name") or "").lower() for obj in battlefield)
            if not found:
                problems.append(f"no_target_matching:{t.get('filter')}")
        else:
            problems.append("invalid_target_spec")

    # Naive legality: if oracle mentions "target creature" but chosen target is not a creature
    if "target creature" in oracle.lower():
        for t in targets:
            if t.get("id"):
                obj = next((o for o in battlefield if o.get("id") == t.get("id")), None)
                if obj:
                    # attempt to check 'type_line' on object if present
                    typ = (obj.get("type_line") or "").lower()
                    if "creature" not in typ:
                        problems.append(f"target_not_creature:{t.get('id')}")

    res = {"valid": len(problems) == 0, "problems": problems}
    logger.info({"action": "validate_targets", "spell": spell.get("card_name"), "result": res})
    return res


def resolve_stack(state: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve the top of the stack with improved parsing for common effects.

    The resolver remains conservative and only handles a few patterns.
    """
    stack = state.get("stack", [])[:]
    battlefield = state.get("battlefield", [])
    effects: List[str] = []
    if not stack:
        return {"state": state, "effects": ["stack_empty"]}

    top = stack.pop()
    card_name = top.get("card_name")
    card = _fetch_card(card_name) if card_name else None
    oracle = (card.get("oracle_text") if card else top.get("oracle_text", "")) or ""

    # handle destroy target
    if "destroy target" in oracle.lower():
        t = top.get("targets", [])[:1]
        if t:
            tid = t[0].get("id")
            battlefield = [obj for obj in battlefield if obj.get("id") != tid]
            effects.append(f"destroyed:{tid}")
        else:
            effects.append("destroy_no_target")

    # handle deal X damage
    if "deal" in oracle.lower() and "damage" in oracle.lower():
        m = re.search(r"(\d+)", oracle)
        if m:
            dmg = int(m.group(1))
            t = top.get("targets", [])[:1]
            if t:
                tid = t[0].get("id")
                players = state.get("players", [])
                p = next((pl for pl in players if pl.get("id") == tid or pl.get("name") == tid), None)
                if p:
                    p["life"] = p.get("life", 0) - dmg
                    effects.append(f"dealt:{dmg}_to_player:{p.get('name')}")
                else:
                    for obj in battlefield:
                        if obj.get("id") == tid:
                            obj["damage"] = obj.get("damage", 0) + dmg
                            effects.append(f"dealt:{dmg}_to_object:{tid}")
            else:
                effects.append("deal_damage_no_target")

    new_state = dict(state)
    new_state["stack"] = stack
    new_state["battlefield"] = battlefield
    res = {"state": new_state, "effects": effects, "resolved": top}
    logger.info({"action": "resolve_stack", "resolved": top.get("card_name"), "effects": effects})
    return res


def compute_combat_damage(state: Dict[str, Any]) -> Dict[str, Any]:
    attackers = state.get("attackers", [])
    battlefield = state.get("battlefield", [])
    results = []
    for a in attackers:
        atk_obj = next((o for o in battlefield if o.get("id") == a.get("attacker_id")), None)
        blk_obj = next((o for o in battlefield if o.get("id") == a.get("blocker_id")), None)
        if not atk_obj:
            results.append({"attacker": a.get("attacker_id"), "result": "attacker_not_found"})
            continue
        card = _fetch_card(atk_obj.get("card_name"))
        p_atk = None
        t_atk = None
        if card:
            try:
                p_atk = int(card.get("power")) if card.get("power") else None
                t_atk = int(card.get("toughness")) if card.get("toughness") else None
            except Exception:
                p_atk = None
                t_atk = None

        if not blk_obj:
            results.append({"attacker": atk_obj.get("id"), "damage_to_player": p_atk})
            continue

        card_b = _fetch_card(blk_obj.get("card_name"))
        p_blk = None
        t_blk = None
        if card_b:
            try:
                p_blk = int(card_b.get("power")) if card_b.get("power") else None
                t_blk = int(card_b.get("toughness")) if card_b.get("toughness") else None
            except Exception:
                p_blk = None
                t_blk = None

        if p_atk is not None and t_blk is not None and p_blk is not None and t_atk is not None:
            atk_survives = p_atk < t_blk
            blk_survives = p_blk < t_atk
            results.append({"attacker": atk_obj.get("id"), "blocker": blk_obj.get("id"), "attacker_survives": atk_survives, "blocker_survives": blk_survives})
        else:
            results.append({"attacker": atk_obj.get("id"), "blocker": blk_obj.get("id"), "result": "unknown_stats"})

    res = {"combat_results": results}
    logger.info({"action": "compute_combat_damage", "results": results})
    return res
