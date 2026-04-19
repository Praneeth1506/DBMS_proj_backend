"""
api/routes/memory.py — Memory retrieval endpoint
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.memory import MemoryRetrievalResponse, MemorySummary
from app.services.memory_service import MemoryService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{person_id}", response_model=MemoryRetrievalResponse)
async def get_memory(
    person_id: int,
    user_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    """
    Retrieve past interaction summaries for a person.
    
    Returns the last 3 interaction summaries (DB-only, no LLM calls).
    """
    try:
        memory_service = MemoryService(db)
        
        memory_data = memory_service.get_memory_context(
            person_id=person_id,
            user_id=user_id,
        )
        
        summaries = [
            MemorySummary(
                interaction_id=m["interaction_id"],
                date=m["date"],
                summary=m["summary"],
                location=m["location"],
            )
            for m in memory_data
        ]
        
        return MemoryRetrievalResponse(
            person_id=person_id,
            summaries=summaries,
        )
    
    except Exception as e:
        logger.error(f"Error retrieving memory: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
