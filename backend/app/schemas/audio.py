"""
schemas/audio.py — Pydantic schemas for audio transcription
"""
from pydantic import BaseModel, Field


class AudioTranscribeRequest(BaseModel):
    """POST /api/audio/transcribe — request payload"""
    interaction_id: int = Field(..., gt=0)
    user_id: int = Field(..., gt=0)
    person_id: int | None = Field(None, gt=0)


class AudioTranscribeResponse(BaseModel):
    """POST /api/audio/transcribe — response payload"""
    transcription: str
    interaction_id: int
    message: str = "Audio transcribed successfully"


class MicRecordRequest(BaseModel):
    """POST /api/audio/record — request payload"""
    user_id: int = Field(..., gt=0)
    person_id: int | None = Field(None, gt=0)
    duration_seconds: int = Field(10, ge=1, le=60, description="Recording duration (1-60 seconds)")


class MicRecordResponse(BaseModel):
    """POST /api/audio/record — response payload"""
    transcription: str
    message: str = "Microphone recording processed successfully"
