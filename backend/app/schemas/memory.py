"""
schemas/memory.py — Pydantic schemas for memory retrieval
"""
from pydantic import BaseModel
from datetime import datetime


class MemorySummary(BaseModel):
    """Single interaction summary"""
    interaction_id: int
    date: datetime
    summary: str
    location: str | None = None


class MemoryRetrievalResponse(BaseModel):
    """GET /api/memory/{person_id} — response payload"""
    person_id: int
    summaries: list[MemorySummary] = []
