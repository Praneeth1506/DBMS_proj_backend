"""
models/conversation.py — ORM model for public.conversation
This is the primary "interaction" table in the actual schema.

Schema columns:
  interactionid, userid, personid, interactiondatetime,
  location, conversation (raw TEXT), summarytext, emotiondetected

The spec's two-level session abstraction (interaction + conversation_session) is NOT
in the DB schema. We implement session buffering in application memory (via
APScheduler) and flush the merged summary into `summarytext` at session close.
The `conversation` column accumulates all raw transcript chunks (appended as text).
"""
from datetime import datetime
from sqlalchemy import Integer, Text, String, TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Conversation(Base):
    __tablename__ = "conversation"
    __table_args__ = {"schema": "public"}

    interactionid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    userid: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("public.users.userid")
    )
    personid: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("public.knownperson.personid")
    )
    interactiondatetime: Mapped[datetime | None] = mapped_column(
        TIMESTAMP, default=datetime.utcnow
    )
    location: Mapped[str | None] = mapped_column(String(100))
    conversation: Mapped[str | None] = mapped_column(Text)   # accumulates raw transcript
    summarytext: Mapped[str | None] = mapped_column(Text)    # LLM summary written on close
    emotiondetected: Mapped[str | None] = mapped_column(String(50))  # V2 / optional

    user = relationship("User", back_populates="conversations")
    person = relationship("KnownPerson", back_populates="conversations")
    notes = relationship("Note", back_populates="conversation")
    emotions = relationship("EmotionRecord", back_populates="conversation")
