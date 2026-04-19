"""
api/routes/interactions.py — Interaction lifecycle endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.interaction import (
    InteractionStartRequest,
    InteractionStartResponse,
    InteractionEndRequest,
    InteractionEndResponse,
)
from app.services.interaction_service import InteractionService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/start", response_model=InteractionStartResponse, status_code=201)
async def start_interaction(
    request: InteractionStartRequest,
    db: Session = Depends(get_db),
):
    """
    Start a new interaction when a person is detected.
    
    Creates a conversation record and initializes the first 30-minute session.
    """
    try:
        interaction_service = InteractionService(db)
        
        interaction_id = interaction_service.start_interaction(
            user_id=request.user_id,
            person_id=request.person_id,
            location=request.location,
        )
        
        return InteractionStartResponse(interaction_id=interaction_id)
    
    except ValueError as e:
        # Active interaction already exists
        logger.warning(f"Conflict starting interaction: {e}")
        raise HTTPException(status_code=409, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error starting interaction: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/end", response_model=InteractionEndResponse)
async def end_interaction(
    request: InteractionEndRequest,
    db: Session = Depends(get_db),
):
    """
    End an interaction when a person leaves.
    
    Generates final interaction summary by merging all session summaries.
    """
    try:
        interaction_service = InteractionService(db)
        
        interaction_summary = await interaction_service.end_interaction(
            interaction_id=request.interaction_id,
        )
        
        return InteractionEndResponse(
            interaction_id=request.interaction_id,
            interaction_summary=interaction_summary,
        )
    
    except ValueError as e:
        logger.warning(f"Interaction not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error ending interaction: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
