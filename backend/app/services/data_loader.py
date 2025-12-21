from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..core.config import get_settings


@dataclass
class RuleEntry:
    identifier: str
    text: str


@dataclass
class CardEntry:
    name: str
    oracle_id: Optional[str]
    type_line: Optional[str]
    oracle_text: Optional[str]


@dataclass
class RulingEntry:
    oracle_id: Optional[str]
    comment: str
    published_at: str


class DataStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.rules_path = settings.raw_data_dir / "MagicCompRules 20251114.txt"
        self.cards_path = settings.raw_data_dir / "oracle-cards-20251221100301.json"
        self.rulings_path = settings.raw_data_dir / "rulings-20251221100031.json"

        self.rules: List[RuleEntry] = []
        self.cards: List[CardEntry] = []
        self.rulings: List[RulingEntry] = []

    def load(self) -> None:
        self.rules = self._load_rules(self.rules_path)
        self.cards = self._load_cards(self.cards_path)
        self.rulings = self._load_rulings(self.rulings_path)

    def _load_rules(self, path: Path) -> List[RuleEntry]:
        entries: List[RuleEntry] = []
        rule_pattern = re.compile(r"^(?P<id>\d{1,3}(?:\.\d+[a-z]?)?)\.\s+(?P<text>.+)$")
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                match = rule_pattern.match(line.strip())
                if match:
                    entries.append(
                        RuleEntry(
                            identifier=match.group("id"),
                            text=match.group("text"),
                        )
                    )
        return entries

    def _load_cards(self, path: Path) -> List[CardEntry]:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        cards: List[CardEntry] = []
        for card in payload:
            cards.append(
                CardEntry(
                    name=card.get("name"),
                    oracle_id=card.get("oracle_id"),
                    type_line=card.get("type_line"),
                    oracle_text=card.get("oracle_text"),
                )
            )
        return cards

    def _load_rulings(self, path: Path) -> List[RulingEntry]:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        entries: List[RulingEntry] = []
        for ruling in payload:
            entries.append(
                RulingEntry(
                    oracle_id=ruling.get("oracle_id"),
                    comment=ruling.get("comment", ""),
                    published_at=ruling.get("published_at", ""),
                )
            )
        return entries


datastore = DataStore()
