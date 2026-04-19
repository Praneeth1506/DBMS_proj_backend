"""
api/routes/notes.py — Note creation endpoint
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.note import NoteCreateRequest, NoteCreateResponse
from app.services.note_service import NoteService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=NoteCreateResponse, status_code=201)
async def create_note(
    request: NoteCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Create a note and sync to Google Tasks.
    
    Note is stored in DB and synced to Google Tasks if user has OAuth token.
    """
    try:
        # Get user_id from interaction
        from app.models.conversation import Conversation
        conversation = db.get(Conversation, request.interaction_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Interaction not found")
        
        user_id = conversation.userid
        
        note_service = NoteService(db)
        
        note_id, sync_warning = note_service.create_note(
            interaction_id=request.interaction_id,
            content=request.content,
            user_id=user_id,
        )
        
        return NoteCreateResponse(
            note_id=note_id,
            sync_warning=sync_warning,
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
