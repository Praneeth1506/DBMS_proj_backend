"""
services/emotion_service.py — Business logic for EmotionRecord management
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional

from app.models.emotion_record import EmotionRecord
from app.models.conversation import Conversation

logger = logging.getLogger(__name__)


class EmotionService:
    """Service for managing emotion records"""

    def __init__(self, db: Session):
        self.db = db

    def create_emotion_record(
        self,
        interaction_id: int,
        emotiontype: str,
        confidencelevel: float,
    ) -> EmotionRecord:
        """
        Create a new emotion record for an interaction.
        
        Args:
            interaction_id: Interaction ID
            emotiontype: Type of emotion (e.g., "happy", "sad", "angry")
            confidencelevel: Confidence level (0.0 to 1.0)
        
        Returns:
            Created EmotionRecord object
        
        Raises:
            ValueError: If interaction not found
        """
        # Verify interaction exists
        interaction = self.db.execute(
            select(Conversation).where(Conversation.interactionid == interaction_id)
        ).scalar_one_or_none()
        
        if not interaction:
            raise ValueError(f"Interaction {interaction_id} not found")
        
        emotion = EmotionRecord(
            interactionid=interaction_id,
            emotiontype=emotiontype,
            confidencelevel=confidencelevel,
        )
        
        self.db.add(emotion)
        self.db.commit()
        self.db.refresh(emotion)
        
        logger.info(f"Created emotion record {emotion.emotionid} for interaction {interaction_id}: {emotiontype}")
        return emotion

    def get_emotion_record(self, emotion_id: int) -> Optional[EmotionRecord]:
        """Get emotion record by ID"""
        return self.db.execute(
            select(EmotionRecord).where(EmotionRecord.emotionid == emotion_id)
        ).scalar_one_or_none()

    def get_emotions_for_interaction(self, interaction_id: int) -> list[EmotionRecord]:
        """Get all emotion records for an interaction"""
        return list(
            self.db.execute(
                select(EmotionRecord).where(EmotionRecord.interactionid == interaction_id)
            ).scalars()
        )

    def list_emotion_records(self, skip: int = 0, limit: int = 100) -> list[EmotionRecord]:
        """List all emotion records with pagination"""
        return list(
            self.db.execute(
                select(EmotionRecord).offset(skip).limit(limit)
            ).scalars()
        )

    def count_emotion_records(self) -> int:
        """Count total emotion records"""
        return self.db.query(EmotionRecord).count()

    def delete_emotion_record(self, emotion_id: int) -> bool:
        """
        Delete an emotion record.
        
        Args:
            emotion_id: Emotion record ID to delete
        
        Returns:
            True if deleted, False if not found
        """
        emotion = self.get_emotion_record(emotion_id)
        if not emotion:
            return False
        
        self.db.delete(emotion)
        self.db.commit()
        
        logger.info(f"Deleted emotion record {emotion_id}")
        return True
