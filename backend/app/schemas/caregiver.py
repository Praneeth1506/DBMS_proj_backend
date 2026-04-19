"""
schemas/caregiver.py — Pydantic schemas for Caregiver endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional


class CaregiverBase(BaseModel):
    """Base caregiver schema"""
    name: Optional[str] = Field(None, max_length=100)
    relationshiptouser: Optional[str] = Field(None, max_length=50)
    accesslevel: Optional[str] = Field(None, max_length=20)


class CaregiverCreate(CaregiverBase):
    """Schema for creating a new caregiver"""
    name: str = Field(..., min_length=1, max_length=100)
    relationshiptouser: str = Field(..., max_length=50)
    accesslevel: str = Field(default="read", max_length=20)


class CaregiverUpdate(CaregiverBase):
    """Schema for updating caregiver (all fields optional)"""
    pass


class CaregiverResponse(CaregiverBase):
    """Schema for caregiver response"""
    caregiverid: int

    class Config:
        from_attributes = True


class CaregiverListResponse(BaseModel):
    """Schema for listing caregivers"""
    caregivers: list[CaregiverResponse]
    total: int


class AssignCaregiverRequest(BaseModel):
    """Schema for assigning caregiver to user"""
    user_id: int = Field(..., gt=0)
    caregiver_id: int = Field(..., gt=0)


class UnassignCaregiverRequest(BaseModel):
    """Schema for unassigning caregiver from user"""
    user_id: int = Field(..., gt=0)
    caregiver_id: int = Field(..., gt=0)
