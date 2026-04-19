"""
api/routes/emotions.py — Emotion record management endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.emotion import (
    EmotionRecordCreate,
    EmotionRecordResponse,
    EmotionRecordListResponse,
)
from app.services.emotion_service import EmotionService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=EmotionRecordResponse, status_code=201)
def create_emotion_record(
    emotion_data: EmotionRecordCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new emotion record for an interaction.
    
    This endpoint is typically called by Member A's emotion detection system.
    
    Required fields:
    - interaction_id: ID of the interaction
    - emotiontype: Type of emotion detected (e.g., "happy", "sad", "angry", "neutral")
    - confidencelevel: Confidence level (0.0 to 1.0)
    """
    try:
        service = EmotionService(db)
        emotion = service.create_emotion_record(
            interaction_id=emotion_data.interaction_id,
            emotiontype=emotion_data.emotiontype,
            confidencelevel=emotion_data.confidencelevel,
        )
        return emotion
    
    except ValueError as e:
        logger.warning(f"Emotion record creation failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error creating emotion record: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create emotion record: {str(e)}")


@router.get("/{emotion_id}", response_model=EmotionRecordResponse)
def get_emotion_record(
    emotion_id: int,
    db: Session = Depends(get_db),
):
    """
    Get emotion record by ID.
    """
    service = EmotionService(db)
    emotion = service.get_emotion_record(emotion_id)
    
    if not emotion:
        raise HTTPException(status_code=404, detail=f"Emotion record {emotion_id} not found")
    
    return emotion


@router.get("/interaction/{interaction_id}", response_model=list[EmotionRecordResponse])
def get_emotions_for_interaction(
    interaction_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all emotion records for a specific interaction.
    
    Useful for analyzing emotional patterns during a conversation.
    """
    service = EmotionService(db)
    emotions = service.get_emotions_for_interaction(interaction_id)
    return emotions


@router.get("/", response_model=EmotionRecordListResponse)
def list_emotion_records(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
):
    """
    List all emotion records with pagination.
    """
    service = EmotionService(db)
    emotions = service.list_emotion_records(skip=skip, limit=limit)
    total = service.count_emotion_records()
    
    return EmotionRecordListResponse(emotions=emotions, total=total)


@router.delete("/{emotion_id}", status_code=204)
def delete_emotion_record(
    emotion_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete an emotion record.
    """
    service = EmotionService(db)
    deleted = service.delete_emotion_record(emotion_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Emotion record {emotion_id} not found")
    
    return None
