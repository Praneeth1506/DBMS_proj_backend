"""
schemas/note.py — Pydantic schemas for note creation
"""
from pydantic import BaseModel, Field


class NoteCreateRequest(BaseModel):
    """POST /api/notes — request payload"""
    interaction_id: int = Field(..., gt=0)
    person_id: int | None = Field(None, gt=0)
    content: str = Field(..., min_length=1)


class NoteCreateResponse(BaseModel):
    """POST /api/notes — response payload"""
    note_id: int
    message: str = "Note created successfully"
    sync_warning: str | None = None
