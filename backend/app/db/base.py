"""
db/base.py — SQLAlchemy engine + DeclarativeBase.
All ORM models import Base from here.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def get_engine():
    settings = get_settings()
    return create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,     # health-check connections before use
        pool_size=10,
        max_overflow=20,
        echo=(settings.APP_ENV == "development"),
    )
