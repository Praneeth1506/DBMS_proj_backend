import os
import cv2
import json
import logging
import tempfile
import numpy as np
from typing import Dict, Any, Tuple
from openai import OpenAI

from app.services.face_recognition import face_service as fs
from app.services.voice_app.transcription_service import transcribe_audio
from app.database.db import save_conversation

logger = logging.getLogger(__name__)

_openai_client = None

def get_openai_client():
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY is not set. Summarization will fallback.")
            return None
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client

def summarize_conversation_and_emotion(text: str) -> Tuple[str, str]:
    if not text or not text.strip() or len(text.strip()) < 2:
        return "No conversation detected.", "Neutral"

    client = get_openai_client()
    if not client:
        return "Summary unavailable (missing OpenAI key).", "Neutral"

    prompt = f"""
    Analyze the following conversation text:
    "{text}"

    Please provide a structured JSON response with exactly two keys:
    1. "summary": A very brief 1-sentence summary of what was discussed.
    2. "emotion": The single most dominant emotion detected (e.g. Happy, Concerned, Neutral, Angry, Sad, Enthusiastic).

    Respond ONLY in valid JSON.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        summary = data.get("summary", "No summary.")
        emotion = data.get("emotion", "Neutral")
        return summary, emotion

    except Exception as e:
        logger.error(f"OpenAI error during summarize/emotion: {e}")
        return "Summary failed.", "Neutral"

def check_face_fast(frame_bytes: bytes) -> bool:
    """
    Ultra-fast, thread-safe detector for the 1-FPS frontend polling.
    Uses pure OpenCV Haar Cascades to avoid PyTorch/MPS threading deadlocks on Mac.
    """
    import cv2
    import numpy as np
    from app.services.face_recognition.face_service import get_face_cascade
    
    np_arr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is None:
        return False
        
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cascade = get_face_cascade()
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    
    return len(faces) > 0

def process_interaction_payload(userid: int, frame_bytes: bytes, audio_bytes: bytes) -> Dict[str, Any]:
    """
    Option A workflow: receives the captured frame and audio from the browser,
    runs the ML pipeline, and stores interaction if known.
    """
    # 1. Image Processing
    np_arr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is None:
        return {"error": "Invalid image payload."}

    detected, bbox = fs.detect_person(frame)
    if not detected:
        return {"error": "No person detected in the provided frame."}

    face_image = fs.crop_face(frame, bbox)
    if face_image is None:
        return {"error": "Person detected, but face not visible / crop failed."}

    embedding = fs.generate_embedding(face_image)
    if embedding is None:
        return {"error": "Could not generate face embedding."}

    # 2. Audio Processing (Whisper)
    temp_fd, temp_path = tempfile.mkstemp(suffix=".webm")  # Browsers often send webm for audio
    os.close(temp_fd)
    
    transcribed_text = ""
    try:
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)
            
        transcribed_text = transcribe_audio(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # 3. Model Logic
    best_person_id, similarity, match_status = fs.compare_embedding(embedding)
    summary, emotion = summarize_conversation_and_emotion(transcribed_text)

    # 4. Route Execution
    if match_status == "unknown" or best_person_id is None:
        return {
            "status": "needs_registration",
            "message": "Encountered an unknown person.",
            "transcription": transcribed_text,
            "summary": summary,
            "emotion": emotion,
            "embedding": embedding,
            "confidence": round(similarity, 4) if similarity else 0.0
        }

    # Known Person
    details = fs.fetch_details(best_person_id)
    person_name = details["name"] if details else "Unknown"
    
    interaction_id = save_conversation(
        userid=userid,
        personid=best_person_id,
        transcribed_text=transcribed_text,
        summarized_text=summary,
        detected_emotion=emotion,
        location="Living Room via Dashboard"
    )

    return {
        "status": "success",
        "message": f"Interaction recorded with known person: {person_name}.",
        "match_status": match_status,
        "person_name": person_name,
        "relationship_type": details["relationship"] if details else None,
        "confidence": similarity,
        "transcription": transcribed_text,
        "summary": summary,
        "emotion": emotion,
        "interactionid": interaction_id
    }
