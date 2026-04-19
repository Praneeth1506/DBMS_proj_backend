"""
services/session_service.py — Session management with APScheduler timers
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.user import User
from app.models.person import KnownPerson
from app.core.scheduler import get_scheduler
from app.services.llm_service import LLMService
from app.config import get_settings

logger = logging.getLogger(__name__)


class SessionState:
    """In-memory state for an active session"""
    def __init__(self, interaction_id: int, session_number: int, user_id: int, person_id: int):
        self.interaction_id = interaction_id
        self.session_number = session_number
        self.user_id = user_id
        self.person_id = person_id
        self.session_summaries: List[str] = []  # Accumulates summaries for this interaction
        self.started_at = datetime.utcnow()


class SessionManager:
    """
    Manages 30-minute session boundaries using APScheduler.
    
    Architecture:
    - Active sessions tracked in-memory (lost on restart)
    - Transcripts accumulated in DB (conversation.conversation column)
    - Session summaries stored in-memory buffer
    - On interaction end, all session summaries merged into conversation.summarytext
    """
    
    # Class-level state (shared across all instances)
    _active_sessions: Dict[int, SessionState] = {}  # interaction_id -> SessionState
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.scheduler = get_scheduler()
        self.llm_service = LLMService()

    def start_session(
        self,
        interaction_id: int,
        user_id: int,
        person_id: int,
        session_number: int = 1,
    ) -> None:
        """
        Start a new session with a 30-minute timer.
        
        Args:
            interaction_id: DB interaction ID
            user_id: User ID
            person_id: Person ID
            session_number: Session number (1, 2, 3, ...)
        """
        # Create session state
        session_state = SessionState(
            interaction_id=interaction_id,
            session_number=session_number,
            user_id=user_id,
            person_id=person_id,
        )
        self._active_sessions[interaction_id] = session_state
        
        # Schedule timer to expire after SESSION_DURATION_MINUTES
        run_at = datetime.utcnow() + timedelta(minutes=self.settings.SESSION_DURATION_MINUTES)
        
        self.scheduler.add_job(
            func=self._on_session_timer_expire,
            trigger='date',
            run_date=run_at,
            args=[interaction_id],
            id=f"session_timer_{interaction_id}_{session_number}",
            replace_existing=True,
        )
        
        logger.info(
            f"Started session {session_number} for interaction {interaction_id}, "
            f"timer expires at {run_at}"
        )

    async def append_transcript(self, interaction_id: int, transcript_chunk: str) -> None:
        """
        Append transcript chunk to the conversation.conversation column.
        
        Args:
            interaction_id: DB interaction ID
            transcript_chunk: Text to append
        
        Raises:
            ValueError: If no active session exists for this interaction
        """
        # Check if session is active
        if interaction_id not in self._active_sessions:
            raise ValueError(f"No active session for interaction {interaction_id}")
        
        # Append to DB
        conversation = self.db.get(Conversation, interaction_id)
        if not conversation:
            raise ValueError(f"Conversation {interaction_id} not found in database")
        
        if conversation.conversation is None:
            conversation.conversation = transcript_chunk
        else:
            conversation.conversation += "\n" + transcript_chunk
        
        self.db.commit()
        logger.debug(f"Appended transcript to interaction {interaction_id}")

    async def _on_session_timer_expire(self, interaction_id: int) -> None:
        """
        Called by APScheduler when a session timer expires.
        
        This method:
        1. Retrieves the accumulated transcript from DB
        2. Generates a session summary via LLM
        3. Stores summary in in-memory buffer
        4. Checks if person is still present (for now, assume they are)
        5. Starts a new session if person is still present
        """
        logger.info(f"Session timer expired for interaction {interaction_id}")
        
        session_state = self._active_sessions.get(interaction_id)
        if not session_state:
            logger.warning(f"Session state not found for interaction {interaction_id}")
            return
        
        # Get conversation from DB
        conversation = self.db.get(Conversation, interaction_id)
        if not conversation or not conversation.conversation:
            logger.warning(f"No transcript found for interaction {interaction_id}, skipping summarization")
            # Start next session anyway
            await self._start_next_session(interaction_id, session_state)
            return
        
        # Get user and person context for LLM
        user = self.db.get(User, session_state.user_id)
        person = self.db.get(KnownPerson, session_state.person_id)
        
        user_context = user.medicalcondition if user else None
        person_relationship = person.relationshiptype if person else None
        
        # Generate session summary
        try:
            summary = await self.llm_service.summarize_session(
                transcript=conversation.conversation,
                user_context=user_context,
                person_relationship=person_relationship,
            )
            session_state.session_summaries.append(summary)
            logger.info(f"Generated session {session_state.session_number} summary for interaction {interaction_id}")
        except Exception as e:
            logger.error(f"Failed to generate session summary: {e}")
            session_state.session_summaries.append("[Session summary generation failed]")
        
        # For V1, assume person is still present and start next session
        # In production, you'd check with Member A's detection system
        await self._start_next_session(interaction_id, session_state)

    async def _start_next_session(self, interaction_id: int, session_state: SessionState) -> None:
        """Start the next session for an ongoing interaction"""
        next_session_number = session_state.session_number + 1
        self.start_session(
            interaction_id=interaction_id,
            user_id=session_state.user_id,
            person_id=session_state.person_id,
            session_number=next_session_number,
        )

    def cancel_session_timer(self, interaction_id: int) -> None:
        """
        Cancel the active session timer for an interaction.
        
        Called when person leaves (interaction ends).
        """
        session_state = self._active_sessions.get(interaction_id)
        if not session_state:
            logger.warning(f"No active session to cancel for interaction {interaction_id}")
            return
        
        job_id = f"session_timer_{interaction_id}_{session_state.session_number}"
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Cancelled session timer {job_id}")
        except Exception as e:
            logger.debug(f"Timer {job_id} already fired or doesn't exist: {e}")

    def get_session_summaries(self, interaction_id: int) -> List[str]:
        """Get all session summaries for an interaction"""
        session_state = self._active_sessions.get(interaction_id)
        if not session_state:
            return []
        return session_state.session_summaries.copy()

    def clear_session_state(self, interaction_id: int) -> None:
        """Clear in-memory session state after interaction ends"""
        if interaction_id in self._active_sessions:
            del self._active_sessions[interaction_id]
            logger.info(f"Cleared session state for interaction {interaction_id}")

    @classmethod
    def clear_all_sessions(cls) -> None:
        """Clear all active sessions (called on startup recovery)"""
        cls._active_sessions.clear()
        logger.info("Cleared all active session state")
