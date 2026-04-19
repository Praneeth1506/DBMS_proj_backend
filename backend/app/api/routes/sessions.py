"""
api/routes/sessions.py — Session transcript appending endpoint
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.session import SessionAppendRequest, SessionAppendResponse
from app.services.session_service import SessionManager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/append", response_model=SessionAppendResponse)
async def append_transcript(
    request: SessionAppendRequest,
    db: Session = Depends(get_db),
):
    """
    Append a transcript chunk to the active session.
    
    Transcript is accumulated in the conversation.conversation column.
    """
    try:
        session_manager = SessionManager(db)
        
        await session_manager.append_transcript(
            interaction_id=request.interaction_id,
            transcript_chunk=request.transcript_chunk,
        )
        
        return SessionAppendResponse()
    
    except ValueError as e:
        logger.warning(f"Session not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error appending transcript: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
