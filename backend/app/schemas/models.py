from pydantic import BaseModel


class ModelListResponse(BaseModel):
    current: str
    available: list[str]


class ModelSelectionRequest(BaseModel):
    model: str
