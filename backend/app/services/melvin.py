from __future__ import annotations

import heapq
import re
from dataclasses import asdict
from typing import Dict, List

from .data_loader import datastore, RuleEntry, CardEntry, RulingEntry


def _tokenize(text: str) -> List[str]:
    return [token for token in re.findall(r"[A-Za-z]{3,}", text.lower())]


def _score_text(text: str, keywords: List[str]) -> int:
    haystack = text.lower()
    score = 0
    for token in keywords:
        if token in haystack:
            score += 1
    return score


class MelvinService:
    def __init__(self) -> None:
        self._ensure_loaded()

    def _ensure_loaded(self) -> None:
        if not datastore.rules or not datastore.cards or not datastore.rulings:
            datastore.load()

    def answer_question(self, question: str, limit: int = 3) -> Dict[str, List[Dict]]:
        keywords = _tokenize(question)
        rule_hits = self._top_hits(datastore.rules, keywords, limit, lambda entry: entry.text)
        card_hits = self._top_hits(datastore.cards, keywords, limit, lambda entry: entry.oracle_text or "")
        ruling_hits = self._top_hits(datastore.rulings, keywords, limit, lambda entry: entry.comment)

        return {
            "rules": [asdict(entry) for entry in rule_hits],
            "cards": [asdict(entry) for entry in card_hits],
            "rulings": [asdict(entry) for entry in ruling_hits],
        }

    def _top_hits(self, entries, keywords: List[str], limit: int, text_getter):
        if not keywords:
            return entries[:limit]

        heap = []
        for entry in entries:
            text = text_getter(entry)
            if not text:
                continue
            score = _score_text(text, keywords)
            if score == 0:
                continue
            if len(heap) < limit:
                heapq.heappush(heap, (score, entry))
            else:
                heapq.heappushpop(heap, (score, entry))
        heap.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in heap]


melvin_service = MelvinService()
