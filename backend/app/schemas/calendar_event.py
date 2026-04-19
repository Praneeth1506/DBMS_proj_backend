"""
schemas/calendar_event.py — Pydantic schemas for calendar event creation
"""
from pydantic import BaseModel, Field
from datetime import datetime


class CalendarEventCreateRequest(BaseModel):
    """POST /api/calendar/events — request payload"""
    user_id: int = Field(..., gt=0)
    related_person_id: int | None = Field(None, gt=0)
    event_title: str = Field(..., min_length=1, max_length=100)
    event_datetime: datetime
    reminder_time: datetime | None = None


class CalendarEventCreateResponse(BaseModel):
    """POST /api/calendar/events — response payload"""
    event_id: int
    message: str = "Calendar event created successfully"
    sync_warning: str | None = None
