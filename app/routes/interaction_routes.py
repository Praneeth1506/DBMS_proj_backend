import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.ai_models.interaction.interaction_service import process_interaction_payload, check_face_fast
from app.database.db import (
    save_person,
    save_faceencoding,
    save_userknownperson,
    save_conversation
)

interaction_router = APIRouter(prefix="/api/interaction", tags=["Interaction"])

# In-memory dictionary to hold data for unknown persons temporarily.
# In production, this should be Redis or a temp DB table.
temp_sessions: Dict[str, Dict[str, Any]] = {}

class ResolveUnknownRequest(BaseModel):
    session_id: str
    userid: int = 1
    name: str
    relationship_type: str


@interaction_router.post("/detect_person")
async def detect_person(frame: UploadFile = File(...)):
    """
    Lightweight endpoint for frontend to ping 1-FPS to check if a person is in the frame.
    Returns: {"person_detected": true/false}
    """
    frame_bytes = await frame.read()
    detected = await run_in_threadpool(check_face_fast, frame_bytes)
    return JSONResponse({"person_detected": detected})


@interaction_router.post("/process")
async def process_interaction(
    userid: int = Form(1),
    frame: UploadFile = File(...),
    audio: UploadFile = File(...)
):
    """
    Called by the dashboard after recording the conversation.
    Runs the full YOLO → DeepFace → Whisper → Summarization pipeline.
    """
    frame_bytes = await frame.read()
    audio_bytes = await audio.read()

    result = await run_in_threadpool(process_interaction_payload, userid, frame_bytes, audio_bytes)

    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])

    if result.get("status") == "needs_registration":
        session_id = str(uuid.uuid4())
        
        # Save state temporarily
        temp_sessions[session_id] = {
            "embedding": result["embedding"],
            "transcription": result["transcription"],
            "summary": result["summary"],
            "emotion": result["emotion"],
            "confidence": result["confidence"],
        }
        
        # Remove embedding from response to keep JSON light
        response_payload = result.copy()
        del response_payload["embedding"]
        response_payload["temp_session_id"] = session_id
        
        return JSONResponse(response_payload)

    # If known person, just return success
    return JSONResponse(result)


@interaction_router.post("/resolve_unknown")
def resolve_unknown(body: ResolveUnknownRequest):
    """
    Completes the registration for a previously unknown person.
    Requires the `session_id` returned from `/process`.
    """
    if body.session_id not in temp_sessions:
        raise HTTPException(status_code=404, detail="Session expired or invalid.")

    session_data = temp_sessions.pop(body.session_id)

    try:
        # 1. Save to knownperson
        new_person_id = save_person(
            name=body.name,
            relationship_type=body.relationship_type
        )
        if not new_person_id:
            raise Exception("Failed to insert into knownperson.")

        # 2. Save face encoding
        save_faceencoding(
            personid=new_person_id,
            embedding_vector=session_data["embedding"],
            confidencescore=session_data["confidence"]
        )

        # 3. Save userknownperson mapping
        save_userknownperson(userid=body.userid, personid=new_person_id)

        # 4. Save the conversation that just happened
        interaction_id = save_conversation(
            userid=body.userid,
            personid=new_person_id,
            transcribed_text=session_data["transcription"],
            summarized_text=session_data["summary"],
            detected_emotion=session_data["emotion"],
            location="Living Room via Dashboard"
        )

        return JSONResponse({
            "message": f"Successfully registered and saved interaction for {body.name}.",
            "personid": new_person_id,
            "interactionid": interaction_id
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
