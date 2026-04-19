"""
schemas/interaction.py — Pydantic schemas for interaction lifecycle
"""
from pydantic import BaseModel, Field


class InteractionStartRequest(BaseModel):
    """POST /api/interactions/start — request payload"""
    user_id: int = Field(..., gt=0)
    person_id: int = Field(..., gt=0)
    location: str | None = Field(None, max_length=100)


class InteractionStartResponse(BaseModel):
    """POST /api/interactions/start — response payload"""
    interaction_id: int
    message: str = "Interaction started successfully"


class InteractionEndRequest(BaseModel):
    """POST /api/interactions/end — request payload"""
    interaction_id: int = Field(..., gt=0)


class InteractionEndResponse(BaseModel):
    """POST /api/interactions/end — response payload"""
    interaction_id: int
    interaction_summary: str
    message: str = "Interaction ended successfully"
