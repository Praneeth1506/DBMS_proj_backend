"""
services/google_calendar.py — Google Calendar API integration
"""
import logging
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import get_settings

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Service for syncing events to Google Calendar"""

    def __init__(self):
        self.settings = get_settings()

    def create_event(
        self,
        summary: str,
        start_datetime: datetime,
        end_datetime: datetime | None = None,
        reminder_minutes: int | None = None,
        user_token_json: dict | None = None,
    ) -> tuple[bool, str | None]:
        """
        Create an event in Google Calendar.
        
        Args:
            summary: Event title
            start_datetime: Event start time
            end_datetime: Event end time (defaults to start + 1 hour)
            reminder_minutes: Minutes before event to send reminder
            user_token_json: User's OAuth2 token (from users.google_token_json)
        
        Returns:
            (success: bool, event_id: str | None)
        """
        if not user_token_json:
            logger.warning("No Google token provided, skipping Calendar sync")
            return False, None
        
        try:
            # Build credentials from token
            creds = Credentials.from_authorized_user_info(user_token_json)
            
            # Build Calendar API service
            service = build('calendar', 'v3', credentials=creds)
            
            # Default end time to 1 hour after start
            if end_datetime is None:
                from datetime import timedelta
                end_datetime = start_datetime + timedelta(hours=1)
            
            # Build event
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            # Add reminder if specified
            if reminder_minutes is not None:
                event['reminders'] = {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': reminder_minutes},
                    ],
                }
            
            # Create event
            result = service.events().insert(
                calendarId=self.settings.CALENDAR_ID,
                body=event
            ).execute()
            
            event_id = result.get('id')
            logger.info(f"Created Google Calendar event: {event_id}")
            return True, event_id
        
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return False, None
        
        except Exception as e:
            logger.error(f"Unexpected error creating Google Calendar event: {e}")
            return False, None
