from fastapi import APIRouter, Depends, HTTPException, status
import requests

from ..core.config import get_settings
from ..dependencies import get_current_admin
from ..schemas.models import ModelListResponse, ModelSelectionRequest
from ..services.melvin import get_melvin_service

router = APIRouter(prefix="/models", tags=["models"])


def _ollama_base_url():
    settings = get_settings()
    return f"http://{settings.ollama_host}:{settings.ollama_port}"


@router.get("/ollama", response_model=ModelListResponse)
def list_ollama_models(
    _: str = Depends(get_current_admin),
) -> ModelListResponse:
    service = get_melvin_service()
    settings = get_settings()
    try:
        resp = requests.get(f"{_ollama_base_url()}/api/tags", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        models = [item.get("name") for item in data.get("models", []) if item.get("name")]
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to reach Ollama: {exc}",
        ) from exc
    return ModelListResponse(current=service.model_name or settings.ollama_model, available=models)


@router.post("/ollama", response_model=ModelListResponse)
def select_ollama_model(
    payload: ModelSelectionRequest,
    _: str = Depends(get_current_admin),
) -> ModelListResponse:
    service = get_melvin_service()
    settings = get_settings()
    try:
        resp = requests.get(f"{_ollama_base_url()}/api/tags", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        models = [item.get("name") for item in data.get("models", []) if item.get("name")]
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to reach Ollama: {exc}",
        ) from exc

    if payload.model not in models:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Requested model is not available in Ollama")

    service.set_model(payload.model)
    return ModelListResponse(current=service.model_name or settings.ollama_model, available=models)
