"""
models/note.py — ORM model for public.note
Schema columns: noteid, interactionid, content, createdat, importancelevel (INTEGER)

Note: importancelevel is stored as INTEGER in the actual schema, not a string enum.
Convention: 1=low, 2=medium, 3=high
"""
from datetime import datetime
from sqlalchemy import Integer, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Note(Base):
    __tablename__ = "note"
    __table_args__ = {"schema": "public"}

    noteid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interactionid: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("public.conversation.interactionid")
    )
    content: Mapped[str | None] = mapped_column(Text)
    createdat: Mapped[datetime | None] = mapped_column(
        TIMESTAMP, default=datetime.utcnow
    )
    importancelevel: Mapped[int | None] = mapped_column(Integer)  # 1=low, 2=medium, 3=high

    conversation = relationship("Conversation", back_populates="notes")
