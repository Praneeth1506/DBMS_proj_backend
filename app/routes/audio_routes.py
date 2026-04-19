from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
from app.controllers.audio_controller import process_audio_upload, record_audio_from_mic

audio_router = APIRouter(prefix="/api/audio", tags=["Audio"])


@audio_router.post("/upload")
async def audio_upload(
    audio: UploadFile = File(..., description="Audio file to transcribe (WAV/MP3)"),
    userid: int = Form(1),
    personid: Optional[int] = Form(None),
):
    """
    Upload an audio file for transcription.

    - **audio**: WAV or MP3 file
    - **userid**: ID of the user (default: 1)
    - **personid**: ID of the person being spoken to (optional)
    """
    return await process_audio_upload(audio=audio, userid=userid, personid=personid)


@audio_router.post("/record_from_mic")
def audio_record_from_mic(
    userid: int = 1,
    personid: Optional[int] = None,
):
    """
    Record from the server's microphone using Voice Activity Detection.

    The endpoint waits until speech is detected, records while speaking,
    and stops automatically after ~1.5 s of silence.

    Send as query params: `?userid=1&personid=3`
    """
    return record_audio_from_mic(userid=userid, personid=personid)
