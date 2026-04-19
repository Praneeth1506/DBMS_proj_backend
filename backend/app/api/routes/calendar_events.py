"""
api/routes/calendar_events.py — Calendar event creation endpoint
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.calendar_event import CalendarEventCreateRequest, CalendarEventCreateResponse
from app.services.calendar_service import CalendarService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/events", response_model=CalendarEventCreateResponse, status_code=201)
async def create_calendar_event(
    request: CalendarEventCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Create a calendar event and sync to Google Calendar.
    
    Event is stored in DB and synced to Google Calendar if user has OAuth token.
    """
    try:
        calendar_service = CalendarService(db)
        
        event_id, sync_warning = calendar_service.create_event(
            user_id=request.user_id,
            event_title=request.event_title,
            event_datetime=request.event_datetime,
            related_person_id=request.related_person_id,
            reminder_time=request.reminder_time,
        )
        
        return CalendarEventCreateResponse(
            event_id=event_id,
            sync_warning=sync_warning,
        )
    
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
