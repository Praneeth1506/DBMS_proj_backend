"""
services/calendar_service.py — Calendar event creation and Google Calendar sync
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.calendar_event import CalendarEvent
from app.models.user import User
from app.services.google_calendar import GoogleCalendarService

logger = logging.getLogger(__name__)


class CalendarService:
    """Service for creating calendar events and syncing to Google Calendar"""

    def __init__(self, db: Session):
        self.db = db
        self.google_calendar = GoogleCalendarService()

    def create_event(
        self,
        user_id: int,
        event_title: str,
        event_datetime: datetime,
        related_person_id: int | None = None,
        reminder_time: datetime | None = None,
    ) -> tuple[int, str | None]:
        """
        Create a calendar event and sync to Google Calendar.
        
        Args:
            user_id: User ID
            event_title: Event title
            event_datetime: Event date/time
            related_person_id: Optional related person ID
            reminder_time: Optional reminder time
        
        Returns:
            (event_id, sync_warning)
        """
        # Create event in DB
        event = CalendarEvent(
            userid=user_id,
            relatedpersonid=related_person_id,
            eventtitle=event_title,
            eventdatetime=event_datetime,
            remindertime=reminder_time,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        event_id = event.eventid
        logger.info(f"Created calendar event {event_id}")
        
        # Sync to Google Calendar
        sync_warning = None
        user = self.db.get(User, user_id)
        if user and user.google_token_json:
            # Calculate reminder minutes if reminder_time is set
            reminder_minutes = None
            if reminder_time and event_datetime:
                delta = event_datetime - reminder_time
                reminder_minutes = int(delta.total_seconds() / 60)
            
            success, gcal_event_id = self.google_calendar.create_event(
                summary=event_title,
                start_datetime=event_datetime,
                reminder_minutes=reminder_minutes,
                user_token_json=user.google_token_json,
            )
            if not success:
                sync_warning = "Failed to sync event to Google Calendar"
                logger.warning(f"Event {event_id} created but Google Calendar sync failed")
        else:
            sync_warning = "No Google token available, event not synced to Google Calendar"
            logger.info(f"Event {event_id} created but not synced (no Google token)")
        
        return event_id, sync_warning
