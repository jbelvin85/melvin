from fastapi import APIRouter, Depends, HTTPException, status
import requests
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..dependencies import get_current_admin, get_current_user, get_db
from ..models.user import User
from ..schemas.models import (
    ModelListResponse,
    ModelPreferenceResponse,
    ModelPreferenceUpdate,
    ModelSelectionRequest,
    UserModelPreference,
)
from ..services.melvin import get_melvin_service

router = APIRouter(prefix="/models", tags=["models"])


def _ollama_base_url():
    settings = get_settings()
    return f"http://{settings.ollama_host}:{settings.ollama_port}"


def _fetch_available_models() -> list[str]:
    try:
        resp = requests.get(f"{_ollama_base_url()}/api/tags", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return [item.get("name") for item in data.get("models", []) if item.get("name")]
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to reach Ollama: {exc}",
        ) from exc


def _build_user_model_pref(user: User, default_model: str) -> UserModelPreference:
    return UserModelPreference(
        id=user.id,
        username=user.username,
        is_admin=user.is_admin,
        created_at=user.created_at,
        preferred_model=user.preferred_model,
        effective_model=user.preferred_model or default_model,
    )


@router.get("/ollama", response_model=ModelListResponse)
def list_ollama_models(
    _: User = Depends(get_current_user),
) -> ModelListResponse:
    service = get_melvin_service()
    settings = get_settings()
    models = _fetch_available_models()
    return ModelListResponse(current=service.model_name or settings.ollama_model, available=models)


@router.post("/ollama", response_model=ModelListResponse)
def select_ollama_model(
    payload: ModelSelectionRequest,
    _: User = Depends(get_current_admin),
) -> ModelListResponse:
    service = get_melvin_service()
    settings = get_settings()
    models = _fetch_available_models()

    if payload.model not in models:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Requested model is not available in Ollama")

    service.set_model(payload.model)
    return ModelListResponse(current=service.model_name or settings.ollama_model, available=models)


@router.get("/preferences/me", response_model=ModelPreferenceResponse)
def get_my_model_preference(
    user: User = Depends(get_current_user),
) -> ModelPreferenceResponse:
    service = get_melvin_service()
    effective = user.preferred_model or service.model_name
    return ModelPreferenceResponse(preferred_model=user.preferred_model, effective_model=effective)


@router.post("/preferences/me", response_model=ModelPreferenceResponse)
def set_my_model_preference(
    payload: ModelPreferenceUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ModelPreferenceResponse:
    if payload.model:
        models = _fetch_available_models()
        if payload.model not in models:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Requested model is not available in Ollama")
        user.preferred_model = payload.model
    else:
        user.preferred_model = None
    db.add(user)
    db.commit()
    db.refresh(user)
    service = get_melvin_service()
    effective = user.preferred_model or service.model_name
    return ModelPreferenceResponse(preferred_model=user.preferred_model, effective_model=effective)


@router.get("/preferences/users", response_model=list[UserModelPreference])
def list_user_model_preferences(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[UserModelPreference]:
    service = get_melvin_service()
    default_model = service.model_name
    records = db.query(User).order_by(User.username.asc()).all()
    return [_build_user_model_pref(record, default_model) for record in records]


@router.post("/preferences/users/{user_id}", response_model=UserModelPreference)
def set_user_model_preference(
    user_id: int,
    payload: ModelPreferenceUpdate,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> UserModelPreference:
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if payload.model:
        models = _fetch_available_models()
        if payload.model not in models:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Requested model is not available in Ollama")
        target.preferred_model = payload.model
    else:
        target.preferred_model = None
    db.add(target)
    db.commit()
    db.refresh(target)
    service = get_melvin_service()
    return _build_user_model_pref(target, service.model_name)
