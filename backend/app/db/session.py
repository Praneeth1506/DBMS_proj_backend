"""
db/session.py — Session factory and get_db() FastAPI dependency.
"""
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.db.base import get_engine

# One SessionLocal factory shared across the app — thread-safe
_SessionLocal: sessionmaker | None = None


def _get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields one DB session per request, always closes it."""
    factory = _get_session_factory()
    db: Session = factory()
    try:
        yield db
    finally:
        db.close()
