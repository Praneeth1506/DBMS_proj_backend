"""
schemas/session.py — Pydantic schemas for session transcript appending
"""
from pydantic import BaseModel, Field, field_validator


class SessionAppendRequest(BaseModel):
    """POST /api/sessions/append — request payload"""
    interaction_id: int = Field(..., gt=0)
    transcript_chunk: str = Field(..., min_length=1, max_length=10000)

    @field_validator("transcript_chunk")
    @classmethod
    def validate_transcript_length(cls, v: str) -> str:
        if len(v) > 10000:
            raise ValueError("Transcript chunk cannot exceed 10,000 characters")
        return v


class SessionAppendResponse(BaseModel):
    """POST /api/sessions/append — response payload"""
    message: str = "Transcript appended successfully"
