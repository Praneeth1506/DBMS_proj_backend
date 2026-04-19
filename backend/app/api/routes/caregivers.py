"""
api/routes/caregivers.py — Caregiver management endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.caregiver import (
    CaregiverCreate,
    CaregiverUpdate,
    CaregiverResponse,
    CaregiverListResponse,
    AssignCaregiverRequest,
    UnassignCaregiverRequest,
)
from app.services.caregiver_service import CaregiverService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=CaregiverResponse, status_code=201)
def create_caregiver(
    caregiver_data: CaregiverCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new caregiver.
    
    Required fields:
    - name: Caregiver's full name
    - relationshiptouser: Relationship to user (e.g., "spouse", "child", "nurse")
    
    Optional fields:
    - accesslevel: Access level (default: "read")
    """
    try:
        service = CaregiverService(db)
        caregiver = service.create_caregiver(
            name=caregiver_data.name,
            relationshiptouser=caregiver_data.relationshiptouser,
            accesslevel=caregiver_data.accesslevel,
        )
        return caregiver
    
    except Exception as e:
        logger.error(f"Error creating caregiver: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create caregiver: {str(e)}")


@router.get("/{caregiver_id}", response_model=CaregiverResponse)
def get_caregiver(
    caregiver_id: int,
    db: Session = Depends(get_db),
):
    """
    Get caregiver by ID.
    """
    service = CaregiverService(db)
    caregiver = service.get_caregiver(caregiver_id)
    
    if not caregiver:
        raise HTTPException(status_code=404, detail=f"Caregiver {caregiver_id} not found")
    
    return caregiver


@router.get("/", response_model=CaregiverListResponse)
def list_caregivers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
):
    """
    List all caregivers with pagination.
    """
    service = CaregiverService(db)
    caregivers = service.list_caregivers(skip=skip, limit=limit)
    total = service.count_caregivers()
    
    return CaregiverListResponse(caregivers=caregivers, total=total)


@router.put("/{caregiver_id}", response_model=CaregiverResponse)
def update_caregiver(
    caregiver_id: int,
    caregiver_data: CaregiverUpdate,
    db: Session = Depends(get_db),
):
    """
    Update caregiver information.
    
    All fields are optional. Only provided fields will be updated.
    """
    try:
        service = CaregiverService(db)
        caregiver = service.update_caregiver(
            caregiver_id=caregiver_id,
            name=caregiver_data.name,
            relationshiptouser=caregiver_data.relationshiptouser,
            accesslevel=caregiver_data.accesslevel,
        )
        return caregiver
    
    except ValueError as e:
        logger.warning(f"Caregiver update failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error updating caregiver: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update caregiver: {str(e)}")


@router.delete("/{caregiver_id}", status_code=204)
def delete_caregiver(
    caregiver_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a caregiver.
    
    This will also remove all user-caregiver assignments.
    """
    service = CaregiverService(db)
    deleted = service.delete_caregiver(caregiver_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Caregiver {caregiver_id} not found")
    
    return None


@router.post("/assign", status_code=200)
def assign_caregiver(
    request: AssignCaregiverRequest,
    db: Session = Depends(get_db),
):
    """
    Assign a caregiver to a user.
    
    Creates a relationship in the usercaregiver junction table.
    """
    try:
        service = CaregiverService(db)
        service.assign_caregiver_to_user(
            user_id=request.user_id,
            caregiver_id=request.caregiver_id,
        )
        return {"message": f"Caregiver {request.caregiver_id} assigned to user {request.user_id}"}
    
    except ValueError as e:
        logger.warning(f"Caregiver assignment failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error assigning caregiver: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unassign", status_code=200)
def unassign_caregiver(
    request: UnassignCaregiverRequest,
    db: Session = Depends(get_db),
):
    """
    Unassign a caregiver from a user.
    
    Removes the relationship from the usercaregiver junction table.
    """
    try:
        service = CaregiverService(db)
        success = service.unassign_caregiver_from_user(
            user_id=request.user_id,
            caregiver_id=request.caregiver_id,
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Assignment not found for user {request.user_id} and caregiver {request.caregiver_id}"
            )
        
        return {"message": f"Caregiver {request.caregiver_id} unassigned from user {request.user_id}"}
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error unassigning caregiver: {e}")
        raise HTTPException(status_code=500, detail=str(e))
