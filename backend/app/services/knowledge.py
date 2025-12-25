from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional

from ..core.config import get_settings


class KnowledgeStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.metadata_path = settings.processed_data_dir / "knowledge" / "card_metadata.json"
        self._card_cache: Dict[str, Dict[str, Any]] | None = None

    def _ensure_loaded(self) -> None:
        if self._card_cache is not None:
            return
        try:
            self._card_cache = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self._card_cache = {}

    def get_card(self, name: str) -> Optional[Dict[str, Any]]:
        if not name:
            return None
        self._ensure_loaded()
        key = name.lower()
        return self._card_cache.get(key) if self._card_cache else None


knowledge_store = KnowledgeStore()
