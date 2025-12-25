from __future__ import annotations

import itertools
import re
from typing import Dict, List, Optional

from .knowledge import knowledge_store
from .mana_analyzer import parse_available_mana, parse_mana_cost, spend_mana


def _estimate_mana_gain(oracle_text: str) -> Dict[str, int]:
    """
    Try to detect a simple "{T}: Add {X}{Y}" ability and convert it into a mana gain dict.
    """
    if not oracle_text:
        return {}
    regex = re.compile(r"Add\s+((?:\{[^\}]+\})+)", re.IGNORECASE)
    match = regex.search(oracle_text)
    if not match:
        return {}
    tokens = re.findall(r"\{([^\}]+)\}", match.group(1))
    gain: Dict[str, int] = {}
    for token in tokens:
        symbol = token.upper()
        if symbol in {"W", "U", "B", "R", "G"}:
            gain[symbol] = gain.get(symbol, 0) + 1
        elif symbol in {"C", "1"}:
            gain["C"] = gain.get("C", 0) + (1 if symbol == "C" else 1)
        else:
            try:
                gain["C"] = gain.get("C", 0) + int(symbol)
            except ValueError:
                continue
    return gain


def _format_pool(pool: Dict[str, int]) -> str:
    return ", ".join(f"{color}:{qty}" for color, qty in pool.items() if qty > 0) or "none"


def analyze_sequences(question: str, card_names: List[str]) -> Optional[str]:
    if len(card_names) < 2 or len(card_names) > 4:
        return None
    base_pool = parse_available_mana(question)
    if not base_pool:
        return None
    cards = []
    for name in card_names:
        meta = knowledge_store.get_card(name)
        if not meta:
            continue
        cards.append(
            {
                "name": meta.get("name"),
                "mana_cost": meta.get("mana_cost") or "",
                "oracle_text": meta.get("oracle_text") or "",
            }
        )
    if len(cards) < 2:
        return None

    summaries: List[str] = []
    seen_orders = set()
    for order in itertools.permutations(cards):
        labels = tuple(card["name"] for card in order)
        if labels in seen_orders:
            continue
        seen_orders.add(labels)
        pool = dict(base_pool)
        playable = True
        for card in order:
            colored, generic = parse_mana_cost(card["mana_cost"])
            updated = spend_mana(pool, colored, generic)
            if updated is None:
                playable = False
                break
            pool = updated
            gain = _estimate_mana_gain(card["oracle_text"])
            for color, qty in gain.items():
                pool[color] = pool.get(color, 0) + qty
        label = " → ".join(labels)
        if playable:
            summaries.append(f"Order '{label}' playable, leftover mana { _format_pool(pool)}.")
        else:
            summaries.append(f"Order '{label}' not playable with current mana.")

    return "Sequencer → " + " ".join(summaries) if summaries else None
