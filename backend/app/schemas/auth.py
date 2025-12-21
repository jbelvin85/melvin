from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AccountRequestCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=40)
    password: str = Field(..., min_length=8, description="Must include uppercase, lowercase, number, symbol")


class AccountRequestOut(BaseModel):
    id: int
    username: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ApproveRequest(BaseModel):
    approved_username: Optional[str] = None
