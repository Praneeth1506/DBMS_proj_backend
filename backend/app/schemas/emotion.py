"""
schemas/emotion.py — Pydantic schemas for EmotionRecord endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional


class EmotionRecordBase(BaseModel):
    """Base emotion record schema"""
    emotiontype: Optional[str] = Field(None, max_length=50)
    confidencelevel: Optional[float] = Field(None, ge=0.0, le=1.0)


class EmotionRecordCreate(EmotionRecordBase):
    """Schema for creating a new emotion record"""
    interaction_id: int = Field(..., gt=0)
    emotiontype: str = Field(..., max_length=50)
    confidencelevel: float = Field(..., ge=0.0, le=1.0)


class EmotionRecordResponse(EmotionRecordBase):
    """Schema for emotion record response"""
    emotionid: int
    interactionid: int

    class Config:
        from_attributes = True


class EmotionRecordListResponse(BaseModel):
    """Schema for listing emotion records"""
    emotions: list[EmotionRecordResponse]
    total: int
