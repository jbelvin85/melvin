"""Service for querying the Scryfall API."""

from __future__ import annotations

import requests
import time
from typing import Any, Dict, Optional, Tuple

import json
import redis

from ..core.config import get_settings


class ScryfallService:
    """Simple wrapper around the Scryfall HTTP API."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0):
        settings = get_settings()
        self.base_url = base_url or settings.scryfall_base_url
        self.timeout = timeout
        self._cache: Dict[Tuple[str, str, Tuple[Tuple[str, str], ...]], Tuple[float, Any]] = {}
        self._ttl = int(settings.scryfall_cache_ttl_seconds)
        self._redis = None
        if settings.redis_url:
            try:
                self._redis = redis.from_url(settings.redis_url)
            except Exception:
                self._redis = None

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        params = params or {}
        # Build a cache key from method, path, and sorted params
        key_tuple = ("GET", path, tuple(sorted((k, str(v)) for k, v in params.items())))
        key = "scryfall:" + path + ":" + "+".join(f"{k}={v}" for k, v in sorted(params.items()))
        now = time.time()

        # Try Redis first if configured
        if self._redis:
            try:
                cached = self._redis.get(key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass

        # Fallback to in-process cache
        if key_tuple in self._cache:
            ts, data = self._cache[key_tuple]
            if now - ts < self._ttl:
                return data

        resp = requests.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        # store in caches
        try:
            self._cache[key_tuple] = (now, data)
        except Exception:
            pass
        if self._redis:
            try:
                self._redis.setex(key, self._ttl, json.dumps(data))
            except Exception:
                pass
        return data

    def search(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search for cards using Scryfall's search endpoint."""
        p = {"q": query}
        if params:
            p.update(params)
        return self._get("cards/search", params=p)

    def get_card(self, identifier: str) -> Dict[str, Any]:
        """Get a single card by Scryfall id or multiverse id or named endpoint.

        The identifier can be a Scryfall id, an `named` lookup like `named?fuzzy=...`,
        or a direct path component.
        """
        # If identifier looks like a uuid or contains '/', use as-is; otherwise use named fuzzy
        if "/" in identifier or identifier.startswith("named"):
            path = identifier
        else:
            # use the named fuzzy lookup for convenience
            return self._get("cards/named", params={"fuzzy": identifier})

        return self._get(path)

    def autocomplete(self, query: str) -> Dict[str, Any]:
        """Use the Scryfall autocomplete endpoint."""
        return self._get("cards/autocomplete", params={"q": query})


# Singleton
scryfall_service = ScryfallService()
