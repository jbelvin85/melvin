from __future__ import annotations

from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.database import Base, SessionLocal, engine
from ..core.security import hash_password
from ..models.user import User
from .banned_cards import banned_cards_service


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_admin_exists()
    load_banned_cards()


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


def load_banned_cards() -> None:
    """Load banned cards data from JSON file into database."""
    db: Session = SessionLocal()
    try:
        count = banned_cards_service.load_from_json(db)
        if count > 0:
            print(f"Loaded {count} banned cards into database")
    except Exception as e:
        print(f"Error loading banned cards: {e}")
    finally:
        db.close()
