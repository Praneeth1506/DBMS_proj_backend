"""
services/note_service.py — Note creation and Google Tasks sync
"""
import logging
from sqlalchemy.orm import Session

from app.models.note import Note
from app.models.user import User
from app.services.google_tasks import GoogleTasksService

logger = logging.getLogger(__name__)


class NoteService:
    """Service for creating notes and syncing to Google Tasks"""

    def __init__(self, db: Session):
        self.db = db
        self.google_tasks = GoogleTasksService()

    def create_note(
        self,
        interaction_id: int,
        content: str,
        user_id: int,
    ) -> tuple[int, str | None]:
        """
        Create a note and sync to Google Tasks.
        
        Args:
            interaction_id: Interaction ID
            content: Note content
            user_id: User ID (for Google token)
        
        Returns:
            (note_id, sync_warning)
        """
        # Create note in DB
        note = Note(
            interactionid=interaction_id,
            content=content,
        )
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        
        note_id = note.noteid
        logger.info(f"Created note {note_id}")
        
        # Sync to Google Tasks
        sync_warning = None
        user = self.db.get(User, user_id)
        if user and user.google_token_json:
            success, task_id = self.google_tasks.create_task(
                title=content[:100],  # Truncate for title
                notes=content,
                user_token_json=user.google_token_json,
            )
            if not success:
                sync_warning = "Failed to sync note to Google Tasks"
                logger.warning(f"Note {note_id} created but Google Tasks sync failed")
        else:
            sync_warning = "No Google token available, note not synced to Google Tasks"
            logger.info(f"Note {note_id} created but not synced (no Google token)")
        
        return note_id, sync_warning
