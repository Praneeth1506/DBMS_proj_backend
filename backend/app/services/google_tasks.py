"""
services/google_tasks.py — Google Tasks API integration for notes
"""
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import get_settings

logger = logging.getLogger(__name__)


class GoogleTasksService:
    """Service for syncing notes to Google Tasks"""

    def __init__(self):
        self.settings = get_settings()

    def create_task(
        self,
        title: str,
        notes: str | None = None,
        user_token_json: dict | None = None,
    ) -> tuple[bool, str | None]:
        """
        Create a task in Google Tasks.
        
        Args:
            title: Task title
            notes: Task notes/description
            user_token_json: User's OAuth2 token (from users.google_token_json)
        
        Returns:
            (success: bool, task_id: str | None)
        """
        if not user_token_json:
            logger.warning("No Google token provided, skipping Tasks sync")
            return False, None
        
        try:
            # Build credentials from token
            creds = Credentials.from_authorized_user_info(user_token_json)
            
            # Build Tasks API service
            service = build('tasks', 'v1', credentials=creds)
            
            # Create task
            task = {
                'title': title,
            }
            if notes:
                task['notes'] = notes
            
            result = service.tasks().insert(
                tasklist='@default',
                body=task
            ).execute()
            
            task_id = result.get('id')
            logger.info(f"Created Google Task: {task_id}")
            return True, task_id
        
        except HttpError as e:
            logger.error(f"Google Tasks API error: {e}")
            return False, None
        
        except Exception as e:
            logger.error(f"Unexpected error creating Google Task: {e}")
            return False, None
