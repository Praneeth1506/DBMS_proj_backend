"""
api/routes/users.py — User management endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
)
from app.schemas.caregiver import CaregiverResponse
from app.schemas.person import PersonResponse
from app.services.user_service import UserService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new user.
    
    Required fields:
    - name: User's full name
    - email: User's email (must be unique)
    
    Optional fields:
    - age: User's age
    - medicalcondition: Medical condition description
    - emergencycontact: Emergency contact phone number
    """
    try:
        service = UserService(db)
        user = service.create_user(
            name=user_data.name,
            email=user_data.email,
            age=user_data.age,
            medicalcondition=user_data.medicalcondition,
            emergencycontact=user_data.emergencycontact,
        )
        return user
    
    except ValueError as e:
        logger.warning(f"User creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Get user by ID.
    """
    service = UserService(db)
    user = service.get_user(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    return user


@router.get("/", response_model=UserListResponse)
def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
):
    """
    List all users with pagination.
    """
    service = UserService(db)
    users = service.list_users(skip=skip, limit=limit)
    total = service.count_users()
    
    return UserListResponse(users=users, total=total)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
):
    """
    Update user information.
    
    All fields are optional. Only provided fields will be updated.
    """
    try:
        service = UserService(db)
        user = service.update_user(
            user_id=user_id,
            name=user_data.name,
            age=user_data.age,
            medicalcondition=user_data.medicalcondition,
            emergencycontact=user_data.emergencycontact,
            email=user_data.email,
        )
        return user
    
    except ValueError as e:
        logger.warning(f"User update failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a user.
    
    WARNING: This will cascade delete all related data (interactions, notes, etc.)
    """
    service = UserService(db)
    deleted = service.delete_user(user_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    return None


@router.get("/{user_id}/caregivers", response_model=list[CaregiverResponse])
def get_user_caregivers(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all caregivers assigned to a user.
    """
    try:
        service = UserService(db)
        caregivers = service.get_user_caregivers(user_id)
        return caregivers
    
    except ValueError as e:
        logger.warning(f"Failed to get caregivers: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error getting caregivers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/persons", response_model=list[PersonResponse])
def get_user_known_persons(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all known persons for a user.
    """
    try:
        service = UserService(db)
        persons = service.get_user_known_persons(user_id)
        return persons
    
    except ValueError as e:
        logger.warning(f"Failed to get known persons: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error getting known persons: {e}")
        raise HTTPException(status_code=500, detail=str(e))
