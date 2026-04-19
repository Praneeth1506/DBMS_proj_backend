"""
api/routes/persons.py — Person identification and registration endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.person import (
    PersonIdentifyRequest,
    PersonIdentifyResponse,
    PersonRegisterRequest,
    PersonRegisterResponse,
    MemoryContext,
)
from app.services.person_service import PersonService
from app.services.memory_service import MemoryService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/identify", response_model=PersonIdentifyResponse)
async def identify_person(
    request: PersonIdentifyRequest,
    db: Session = Depends(get_db),
):
    """
    Identify a person by face encoding.
    
    Returns person details and memory context if match found (confidence >= 0.6),
    otherwise returns null person_id.
    """
    try:
        person_service = PersonService(db)
        memory_service = MemoryService(db)
        
        # Identify person
        person_id, confidence, person = person_service.identify_person(
            encoding=request.encoding,
            user_id=request.user_id,
        )
        
        if person_id is None:
            # No match found
            return PersonIdentifyResponse(
                person_id=None,
                name=None,
                relationship_type=None,
                priority_level=None,
                confidence=None,
                memory_context=[],
            )
        
        # Get memory context
        memory_data = memory_service.get_memory_context(
            person_id=person_id,
            user_id=request.user_id,
        )
        
        memory_context = [
            MemoryContext(date=m["date"], summary=m["summary"])
            for m in memory_data
        ]
        
        return PersonIdentifyResponse(
            person_id=person_id,
            name=person.name,
            relationship_type=person.relationshiptype,
            priority_level=person.prioritylevel,
            confidence=confidence,
            memory_context=memory_context,
        )
    
    except Exception as e:
        logger.error(f"Error identifying person: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/register", response_model=PersonRegisterResponse, status_code=201)
async def register_person(
    request: PersonRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new person with face encoding.
    """
    try:
        person_service = PersonService(db)
        
        person_id = person_service.register_person(
            user_id=request.user_id,
            name=request.name,
            encoding=request.encoding,
            relationship_type=request.relationship_type,
            priority_level=request.priority_level,
            confidence_score=request.confidence_score,
        )
        
        return PersonRegisterResponse(person_id=person_id)
    
    except Exception as e:
        logger.error(f"Error registering person: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
