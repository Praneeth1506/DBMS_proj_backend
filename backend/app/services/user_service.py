"""
services/user_service.py — Business logic for User management
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional

from app.models.user import User
from app.models.caregiver import Caregiver
from app.models.person import KnownPerson
from app.models.junction_tables import usercaregiver, userknownperson

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing users"""

    def __init__(self, db: Session):
        self.db = db

    def create_user(
        self,
        name: str,
        email: str,
        age: Optional[int] = None,
        medicalcondition: Optional[str] = None,
        emergencycontact: Optional[str] = None,
    ) -> User:
        """
        Create a new user.
        
        Args:
            name: User's name
            email: User's email (must be unique)
            age: User's age
            medicalcondition: Medical condition description
            emergencycontact: Emergency contact phone
        
        Returns:
            Created User object
        
        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists
        existing = self.db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()
        
        if existing:
            raise ValueError(f"User with email {email} already exists")
        
        user = User(
            name=name,
            email=email,
            age=age,
            medicalcondition=medicalcondition,
            emergencycontact=emergencycontact,
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"Created user {user.userid}: {name}")
        return user

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.execute(
            select(User).where(User.userid == user_id)
        ).scalar_one_or_none()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

    def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """List all users with pagination"""
        return list(
            self.db.execute(
                select(User).offset(skip).limit(limit)
            ).scalars()
        )

    def count_users(self) -> int:
        """Count total users"""
        return self.db.query(User).count()

    def update_user(
        self,
        user_id: int,
        name: Optional[str] = None,
        age: Optional[int] = None,
        medicalcondition: Optional[str] = None,
        emergencycontact: Optional[str] = None,
        email: Optional[str] = None,
    ) -> User:
        """
        Update user information.
        
        Args:
            user_id: User ID to update
            name: New name (optional)
            age: New age (optional)
            medicalcondition: New medical condition (optional)
            emergencycontact: New emergency contact (optional)
            email: New email (optional)
        
        Returns:
            Updated User object
        
        Raises:
            ValueError: If user not found or email already exists
        """
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Check email uniqueness if updating
        if email and email != user.email:
            existing = self.get_user_by_email(email)
            if existing:
                raise ValueError(f"Email {email} already in use")
            user.email = email
        
        if name is not None:
            user.name = name
        if age is not None:
            user.age = age
        if medicalcondition is not None:
            user.medicalcondition = medicalcondition
        if emergencycontact is not None:
            user.emergencycontact = emergencycontact
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"Updated user {user_id}")
        return user

    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User ID to delete
        
        Returns:
            True if deleted, False if not found
        """
        user = self.get_user(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        
        logger.info(f"Deleted user {user_id}")
        return True

    def get_user_caregivers(self, user_id: int) -> list[Caregiver]:
        """Get all caregivers assigned to a user"""
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        return user.caregivers

    def get_user_known_persons(self, user_id: int) -> list[KnownPerson]:
        """Get all known persons for a user"""
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        return user.known_persons
