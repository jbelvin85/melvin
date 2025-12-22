# Scryfall Integration

This project includes backend and frontend integration with the Scryfall API.

## Backend

- API endpoints are available under `/api/scryfall`:
  - `/api/scryfall/search?q=...` — full Scryfall search (returns Scryfall response)
  - `/api/scryfall/card/{identifier}` — lookup a card (supports named fuzzy lookups)
  - `/api/scryfall/autocomplete?q=...` — autocomplete suggestions

- Responses are cached in-memory for `scryfall_cache_ttl_seconds` (default 3600s). You can configure this in the backend settings (env or `get_settings()`).

## Chat integration

When a user asks a question that includes a card name, Melvin will attempt an autocomplete lookup and include a short card summary in the card context passed to the model. This improves accuracy for card-specific questions.

## Frontend

A simple search UI is available in the app under the Scryfall search section. It calls the backend endpoints so your API key (if any) is not exposed.

## Notes

- The cache is an in-memory TTL cache; it resets when the backend process restarts. For production, consider replacing with Redis or another persistent cache.
- Respect Scryfall's API terms and rate limits. Add further rate-limiting if your deployment will have high traffic.
