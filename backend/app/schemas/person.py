"""
schemas/person.py — Pydantic schemas for person identification and registration
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class PersonIdentifyRequest(BaseModel):
    """POST /api/persons/identify — request payload"""
    user_id: int = Field(..., gt=0, description="User ID (positive integer)")
    encoding: list[float] = Field(..., min_length=128, max_length=512, description="Face encoding vector (128 or 512 floats)")
    frame_timestamp: datetime | None = Field(None, description="Optional timestamp of the frame")

    @field_validator("encoding")
    @classmethod
    def validate_encoding_length(cls, v: list[float]) -> list[float]:
        """Ensure encoding is exactly 128 or 512 dimensions"""
        if len(v) not in (128, 512):
            raise ValueError("Face encoding must be exactly 128 or 512 dimensions")
        return v


class MemoryContext(BaseModel):
    """Memory context for a past interaction"""
    date: datetime
    summary: str


class PersonIdentifyResponse(BaseModel):
    """POST /api/persons/identify — response payload"""
    person_id: int | None = Field(None, description="Matched person ID, null if no match")
    name: str | None = None
    relationship_type: str | None = None
    priority_level: int | None = None
    confidence: float | None = Field(None, ge=0.0, le=1.0, description="Cosine similarity score")
    memory_context: list[MemoryContext] = Field(default_factory=list, description="Last 3 interaction summaries")


class PersonRegisterRequest(BaseModel):
    """POST /api/persons/register — request payload"""
    user_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=100)
    relationship_type: str | None = Field(None, max_length=50)
    priority_level: int | None = Field(None, ge=1, le=5)
    encoding: list[float] = Field(..., min_length=128, max_length=512)
    confidence_score: float | None = Field(None, ge=0.0, le=1.0)

    @field_validator("encoding")
    @classmethod
    def validate_encoding_length(cls, v: list[float]) -> list[float]:
        if len(v) not in (128, 512):
            raise ValueError("Face encoding must be exactly 128 or 512 dimensions")
        return v


class PersonRegisterResponse(BaseModel):
    """POST /api/persons/register — response payload"""
    person_id: int
    message: str = "Person registered successfully"
