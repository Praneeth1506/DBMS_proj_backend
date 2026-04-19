"""
models/calendar_event.py — ORM model for public.calendarevent
Schema columns: eventid, userid, relatedpersonid, eventtitle, eventdatetime, remindertime
"""
from datetime import datetime
from sqlalchemy import Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class CalendarEvent(Base):
    __tablename__ = "calendarevent"
    __table_args__ = {"schema": "public"}

    eventid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    userid: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("public.users.userid")
    )
    relatedpersonid: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("public.knownperson.personid")
    )
    eventtitle: Mapped[str | None] = mapped_column(String(100))
    eventdatetime: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    remindertime: Mapped[datetime | None] = mapped_column(TIMESTAMP)

    user = relationship("User", back_populates="calendar_events")
    related_person = relationship("KnownPerson", back_populates="calendar_events")
