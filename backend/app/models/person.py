"""
models/person.py — ORM model for public.knownperson
Schema columns: personid, name, relationshiptype, prioritylevel, notes
"""
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class KnownPerson(Base):
    __tablename__ = "knownperson"
    __table_args__ = {"schema": "public"}

    personid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(String(100))
    relationshiptype: Mapped[str | None] = mapped_column(String(50))
    prioritylevel: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    face_encodings = relationship("FaceEncoding", back_populates="person")
    conversations = relationship("Conversation", back_populates="person")
    calendar_events = relationship("CalendarEvent", back_populates="related_person")
    users = relationship(
        "User",
        secondary="public.userknownperson",
        back_populates="known_persons",
    )
