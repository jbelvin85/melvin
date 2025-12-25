from datetime import datetime

from pydantic import BaseModel


class ModelListResponse(BaseModel):
    current: str
    available: list[str]


class ModelSelectionRequest(BaseModel):
    model: str


class ModelPreferenceResponse(BaseModel):
    preferred_model: str | None = None
    effective_model: str


class ModelPreferenceUpdate(BaseModel):
    model: str | None = None


class UserModelPreference(BaseModel):
    id: int
    username: str
    is_admin: bool
    created_at: datetime
    preferred_model: str | None = None
    effective_model: str
