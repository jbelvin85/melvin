from fastapi import APIRouter, HTTPException, Query, Request
from typing import Optional

from ..dependencies import get_db  # keep pattern though not used here
from ..schemas import chat  # placeholder import pattern

from ..services.scryfall import scryfall_service

# Simple in-memory per-IP rate limiter
_RATE_LIMIT_WINDOW = 60  # seconds
_RATE_LIMIT_MAX = 60  # requests per window per IP
_ip_buckets: dict[str, list[float]] = {}

def _rate_limited(request: Request) -> None:
    try:
        ip = request.client.host
    except Exception:
        ip = "unknown"
    import time
    now = time.time()
    bucket = _ip_buckets.get(ip) or []
    # remove old entries
    bucket = [t for t in bucket if now - t < _RATE_LIMIT_WINDOW]
    if len(bucket) >= _RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    bucket.append(now)
    _ip_buckets[ip] = bucket

router = APIRouter(prefix="/scryfall", tags=["scryfall"])


@router.get("/search")
def search(request: Request, q: str = Query(..., min_length=1), unique: Optional[str] = None, order: Optional[str] = None):
    params = {}
    if unique:
        params["unique"] = unique
    if order:
        params["order"] = order

    try:
        _rate_limited(request)
        result = scryfall_service.search(q, params=params)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return result


@router.get("/card/{identifier}")
def get_card(request: Request, identifier: str):
    try:
        _rate_limited(request)
        result = scryfall_service.get_card(identifier)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return result


@router.get("/autocomplete")
def autocomplete(request: Request, q: str = Query(..., min_length=1)):
    try:
        _rate_limited(request)
        result = scryfall_service.autocomplete(q)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return result
