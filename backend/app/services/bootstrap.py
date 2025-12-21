from __future__ import annotations

from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.database import Base, SessionLocal, engine
from ..core.security import hash_password
from ..models.user import User


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_admin_exists()


def ensure_admin_exists() -> None:
    settings = get_settings()
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.username == settings.initial_admin_username).first()
        if user:
            return
        admin_user = User(
            username=settings.initial_admin_username,
            password_hash=hash_password(settings.initial_admin_password),
            is_admin=True,
        )
        db.add(admin_user)
        db.commit()
    finally:
        db.close()
