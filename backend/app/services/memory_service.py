"""
services/memory_service.py — Fast memory retrieval (DB-only, no LLM)
"""
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.models.conversation import Conversation
from app.config import get_settings


class MemoryService:
    """Service for retrieving past interaction summaries"""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def get_memory_context(self, person_id: int, user_id: int) -> list[dict]:
        """
        Retrieve the last N interaction summaries for a person.
        
        Returns:
            List of dicts with keys: interaction_id, date, summary, location
        """
        limit = self.settings.MEMORY_CONTEXT_LIMIT
        
        stmt = (
            select(Conversation)
            .where(
                Conversation.personid == person_id,
                Conversation.userid == user_id,
                Conversation.summarytext.isnot(None),  # Only completed interactions
            )
            .order_by(desc(Conversation.interactiondatetime))
            .limit(limit)
        )
        
        interactions = self.db.execute(stmt).scalars().all()
        
        return [
            {
                "interaction_id": conv.interactionid,
                "date": conv.interactiondatetime,
                "summary": conv.summarytext or "",
                "location": conv.location,
            }
            for conv in interactions
        ]
