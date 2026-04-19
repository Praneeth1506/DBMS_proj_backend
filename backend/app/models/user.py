"""
models/user.py — ORM model for public.users
Schema columns: userid, name, age, medicalcondition, emergencycontact, email, google_token_json, createdat
"""
from datetime import datetime
from sqlalchemy import Integer, String, Text, TIMESTAMP, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    userid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(String(100))
    age: Mapped[int | None] = mapped_column(Integer)
    medicalcondition: Mapped[str | None] = mapped_column(Text)
    emergencycontact: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(150), unique=True)
    google_token_json: Mapped[dict | None] = mapped_column(JSON)
    createdat: Mapped[datetime | None] = mapped_column(
        TIMESTAMP, default=datetime.utcnow
    )

    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    calendar_events = relationship("CalendarEvent", back_populates="user")
    known_persons = relationship(
        "KnownPerson",
        secondary="public.userknownperson",
        back_populates="users",
    )
    caregivers = relationship(
        "Caregiver",
        secondary="public.usercaregiver",
        back_populates="users",
    )
