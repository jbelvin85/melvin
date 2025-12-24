from __future__ import annotations

from typing import List, Optional

from .data_loader import CardEntry, datastore


class CardSearchService:
    """Simple in-memory search against the ingested oracle card data."""

    def _ensure_loaded(self) -> None:
        if not datastore.cards:
            datastore.load()

    def search(self, query: str, limit: int = 10) -> List[CardEntry]:
        self._ensure_loaded()
        prepared = query.strip().lower()
        if not prepared:
            return []

        matches: List[tuple[int, CardEntry]] = []
        for entry in datastore.cards:
            if not entry.name:
                continue
            name_lower = entry.name.lower()
            if prepared in name_lower:
                # Prefer prefix matches, then substring position, then name length.
                position = name_lower.find(prepared)
                matches.append((position, entry))

        # Sort by substring position first, then alphabetically
        matches.sort(key=lambda item: (item[0], item[1].name))
        return [entry for _, entry in matches[:limit]]

    def get_by_name(self, name: str) -> Optional[CardEntry]:
        self._ensure_loaded()
        target = name.strip().lower()
        if not target:
            return None
        for entry in datastore.cards:
            if entry.name and entry.name.lower() == target:
                return entry
        return None

    def resolve_cards(self, names: List[str]) -> List[CardEntry]:
        resolved: List[CardEntry] = []
        seen: set[str] = set()
        for raw in names:
            key = raw.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            entry = self.get_by_name(raw)
            if entry:
                resolved.append(entry)
        return resolved


card_search_service = CardSearchService()
