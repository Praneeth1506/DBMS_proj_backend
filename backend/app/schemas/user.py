"""
schemas/user.py — Pydantic schemas for User endpoints
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserBase(BaseModel):
    """Base user schema"""
    name: Optional[str] = Field(None, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)
    medicalcondition: Optional[str] = None
    emergencycontact: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    """Schema for creating a new user"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr


class UserUpdate(UserBase):
    """Schema for updating user (all fields optional)"""
    pass


class UserResponse(UserBase):
    """Schema for user response"""
    userid: int
    createdat: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for listing users"""
    users: list[UserResponse]
    total: int
