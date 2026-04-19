"""
services/interaction_service.py — Interaction lifecycle management
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.conversation import Conversation
from app.models.user import User
from app.models.person import KnownPerson
from app.services.session_service import SessionManager
from app.services.llm_service import LLMService
from app.config import get_settings

logger = logging.getLogger(__name__)


class InteractionService:
    """Service for managing interaction lifecycle"""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.session_manager = SessionManager(db)
        self.llm_service = LLMService()

    def start_interaction(
        self,
        user_id: int,
        person_id: int,
        location: str | None = None,
    ) -> int:
        """
        Start a new interaction and initialize the first session.
        
        Args:
            user_id: User ID
            person_id: Person ID
            location: Optional location string
        
        Returns:
            interaction_id
        
        Raises:
            ValueError: If an active interaction already exists for this user
        """
        # Check for existing active interaction for this user
        # Active = tracked in SessionManager's in-memory state
        active_interactions = SessionManager._active_sessions
        for interaction_id, session_state in active_interactions.items():
            if session_state.user_id == user_id:
                raise ValueError(
                    f"User {user_id} already has an active interaction {interaction_id}. "
                    "Only one active interaction per user is allowed."
                )
        
        # Create conversation record
        conversation = Conversation(
            userid=user_id,
            personid=person_id,
            interactiondatetime=datetime.utcnow(),
            location=location,
            conversation="",  # Will accumulate transcript chunks
            summarytext=None,  # Will be set when interaction ends
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        interaction_id = conversation.interactionid
        
        # Start first session
        self.session_manager.start_session(
            interaction_id=interaction_id,
            user_id=user_id,
            person_id=person_id,
            session_number=1,
        )
        
        logger.info(f"Started interaction {interaction_id} for user {user_id}, person {person_id}")
        return interaction_id

    async def end_interaction(self, interaction_id: int) -> str:
        """
        End an interaction and generate the final merged summary.
        
        Steps:
        1. Cancel active session timer
        2. Generate summary for current session (if transcript exists)
        3. Merge all session summaries into interaction summary
        4. Store in conversation.summarytext
        5. Clear session state
        
        Args:
            interaction_id: Interaction ID to end
        
        Returns:
            Final interaction summary text
        
        Raises:
            ValueError: If interaction doesn't exist
        """
        conversation = self.db.get(Conversation, interaction_id)
        if not conversation:
            raise ValueError(f"Interaction {interaction_id} not found")
        
        # Cancel timer
        self.session_manager.cancel_session_timer(interaction_id)
        
        # Get session state
        session_state = SessionManager._active_sessions.get(interaction_id)
        if not session_state:
            logger.warning(f"No active session state for interaction {interaction_id}")
            # Return empty summary if no session was active
            conversation.summarytext = "[No conversation recorded]"
            self.db.commit()
            return conversation.summarytext
        
        # Generate summary for current (final) session if transcript exists
        if conversation.conversation:
            user = self.db.get(User, session_state.user_id)
            person = self.db.get(KnownPerson, session_state.person_id)
            
            user_context = user.medicalcondition if user else None
            person_relationship = person.relationshiptype if person else None
            
            try:
                final_session_summary = await self.llm_service.summarize_session(
                    transcript=conversation.conversation,
                    user_context=user_context,
                    person_relationship=person_relationship,
                )
                session_state.session_summaries.append(final_session_summary)
            except Exception as e:
                logger.error(f"Failed to generate final session summary: {e}")
                session_state.session_summaries.append("[Final session summary generation failed]")
        
        # Merge all session summaries
        all_summaries = session_state.session_summaries
        
        if not all_summaries:
            interaction_summary = "[No conversation recorded]"
        else:
            try:
                user = self.db.get(User, session_state.user_id)
                user_context = user.medicalcondition if user else None
                
                interaction_summary = await self.llm_service.merge_session_summaries(
                    session_summaries=all_summaries,
                    user_context=user_context,
                )
            except Exception as e:
                logger.error(f"Failed to merge session summaries: {e}")
                # Fallback: concatenate summaries
                interaction_summary = "\n\n".join([
                    f"Session {i+1}: {s}" for i, s in enumerate(all_summaries)
                ])
        
        # Store in DB
        conversation.summarytext = interaction_summary
        self.db.commit()
        
        # Clear session state
        self.session_manager.clear_session_state(interaction_id)
        
        logger.info(f"Ended interaction {interaction_id}, summary stored")
        return interaction_summary
