from __future__ import annotations

import re
from typing import Dict, List, Tuple, Optional

from .knowledge import knowledge_store


LAND_TO_COLOR = {
    "plains": "W",
    "island": "U",
    "swamp": "B",
    "mountain": "R",
    "forest": "G",
}


def parse_available_mana(text: str) -> Dict[str, int]:
    """
    Parse simple phrases such as "two Islands", "3 Mountains" to build a mana pool.
    Returns counts per color (W/U/B/R/G). Colorless mana is tracked with key "C".
    """
    pool: Dict[str, int] = {}
    if not text:
        return pool
    pattern = re.compile(r"(\b\d+|\btwo|\bthree|\bfour|\bfive|\bsix)\s+([A-Za-z]+)s?\b", re.IGNORECASE)
    word_to_number = {
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "one": 1,
    }
    for match in pattern.finditer(text):
        raw_qty, land_word = match.groups()
        land_key = land_word.lower()
        if land_key not in LAND_TO_COLOR:
            continue
        try:
            qty = int(raw_qty)
        except ValueError:
            qty = word_to_number.get(raw_qty.lower(), 0)
        if qty <= 0:
            continue
        color = LAND_TO_COLOR[land_key]
        pool[color] = pool.get(color, 0) + qty
    return pool


def parse_mana_cost(cost: str) -> Tuple[Dict[str, int], int]:
    """
    Break a mana cost string like "{2}{G}{U}" into colored requirements and colorless requirement.
    """
    colored: Dict[str, int] = {}
    generic = 0
    if not cost:
        return colored, generic
    tokens = re.findall(r"\{([^\}]+)\}", cost)
    for token in tokens:
        upper = token.upper()
        if upper in {"W", "U", "B", "R", "G"}:
            colored[upper] = colored.get(upper, 0) + 1
        else:
            # Treat digits as generic mana. Ignore other symbols for now (X, hybrid, etc.).
            try:
                generic += int(upper)
            except ValueError:
                generic += 0
    return colored, generic


def spend_mana(pool: Dict[str, int], colored: Dict[str, int], generic: int) -> Optional[Dict[str, int]]:
    available = dict(pool)
    for color, needed in colored.items():
        if available.get(color, 0) < needed:
            return None
        available[color] -= needed
    remaining = generic
    for color in ["W", "U", "B", "R", "G"]:
        if remaining <= 0:
            break
        usable = min(available.get(color, 0), remaining)
        available[color] = available.get(color, 0) - usable
        remaining -= usable
    if remaining > 0:
        usable = min(available.get("C", 0), remaining)
        available["C"] = available.get("C", 0) - usable
        remaining -= usable
    if remaining > 0:
        return None
    return available


def can_pay(pool: Dict[str, int], colored: Dict[str, int], generic: int) -> bool:
    return spend_mana(pool, colored, generic) is not None


def explain_mana_check(question: str, card_names: List[str]) -> str | None:
    pool = parse_available_mana(question)
    if not pool or not card_names:
        return None
    requirements: List[str] = []
    colored_total: Dict[str, int] = {}
    generic_total = 0
    for name in card_names:
        meta = knowledge_store.get_card(name)
        if not meta:
            continue
        mana_cost = meta.get("mana_cost") or ""
        colored, generic = parse_mana_cost(mana_cost)
        for color, qty in colored.items():
            colored_total[color] = colored_total.get(color, 0) + qty
        generic_total += generic
        requirements.append(f"{name} {mana_cost or '{0}'}")
    if not requirements:
        return None
    can_cast = can_pay(pool, colored_total, generic_total)
    pool_str = ", ".join(f"{color}:{qty}" for color, qty in pool.items())
    colored_str = ", ".join(f"{color}:{qty}" for color, qty in colored_total.items() if qty > 0) or "None"
    result = "enough mana" if can_cast else "NOT enough mana"
    return (
        f"Mana analyzer → Available ({pool_str or 'none'}). "
        f"Required colored ({colored_str}), generic {generic_total}. "
        f"Cards: {', '.join(requirements)}. Result: {result}."
    )
