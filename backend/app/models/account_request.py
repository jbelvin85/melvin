from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Integer, String

from ..core.database import Base


class AccountRequestStatus(str):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


class AccountRequest(Base):
    __tablename__ = "account_requests"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    status = Column(
        Enum(
            AccountRequestStatus.PENDING,
            AccountRequestStatus.APPROVED,
            AccountRequestStatus.DENIED,
            name="account_request_status",
        ),
        default=AccountRequestStatus.PENDING,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
