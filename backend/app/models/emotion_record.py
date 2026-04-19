"""
models/emotion_record.py — ORM model for public.emotionrecord
Schema columns: emotionid, interactionid, emotiontype, confidencelevel
"""
from sqlalchemy import Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class EmotionRecord(Base):
    __tablename__ = "emotionrecord"
    __table_args__ = {"schema": "public"}

    emotionid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interactionid: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("public.conversation.interactionid")
    )
    emotiontype: Mapped[str | None] = mapped_column(String(50))
    confidencelevel: Mapped[float | None] = mapped_column(Numeric(5, 2))

    # Relationships
    conversation = relationship("Conversation", back_populates="emotions")
