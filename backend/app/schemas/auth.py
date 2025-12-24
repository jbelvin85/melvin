from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AccountRequestCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=40)
    password: str = Field(
        ...,
        min_length=12,
        description="Must include uppercase, lowercase, number, and symbol",
    )

    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        import re

        if len(value) < 12:
            raise ValueError("Password must be at least 12 characters long.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must include an uppercase letter.")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must include a lowercase letter.")
        if not re.search(r"[0-9]", value):
            raise ValueError("Password must include a number.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>\\[\\]\\-_;'+=/~`]", value):
            raise ValueError("Password must include a symbol.")
        return value

    @classmethod
    def model_validate(cls, *args, **kwargs):
        model = super().model_validate(*args, **kwargs)
        model.password = cls.validate_password_strength(model.password)
        return model


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
