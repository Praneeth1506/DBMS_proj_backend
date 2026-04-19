"""
services/ml/session_loop.py
----------------------------
Background thread that continuously:
  1. Captures webcam frames
  2. Detects if a person is present
  3. Generates a face embedding and matches against the DB
  4. Manages the audio recording lifecycle around face presence
  5. On session-end (person leaves for > ABSENCE_TIMEOUT_S), saves the
     full conversation to PostgreSQL

Global state is exposed for the API layer to read (SSE / WebSocket / polling).

State machine:
    WAITING  → face detected → ACTIVE (start audio)
    ACTIVE   → face absent > timeout → SAVING (stop audio, transcribe, save)
    SAVING   → done → WAITING
"""

import os
import time
import threading
from typing import Optional

import cv2
import numpy as np
from dotenv import load_dotenv

from app.services.face_recognition.face_recognition_service import (
    detect_person,
    crop_face,
    get_face_bbox,
    generate_embedding,
    compare_embedding,
)
from app.services.face_recognition.conversation_service import (
    record_audio,
    stop_recording,
    transcribe_audio,
    summarize_conversation,
    save_conversation,
    save_emotion_record,
    get_all_face_encodings,
    get_known_person,
    get_live_transcript,
)

try:
    from app.services.face_recognition.facial_analysis import facial_analyzer
except ImportError:
    facial_analyzer = None

load_dotenv()

USER_ID             = int(os.getenv("USER_ID", "1"))
ABSENCE_TIMEOUT_S   = 5.0   # seconds face must be absent to end a session
FRAME_INTERVAL_S    = 0.20  # ~5 fps detection loop
WEBCAM_INDEX        = 0

# ── Public read-only state ────────────────────────────────────────────────────
_state_lock = threading.Lock()

session_state: dict = {
    "status":            "idle",           # idle | detecting | active | saving
    "person_detected":   False,
    "person_id":         None,
    "person_name":       None,
    "relationship":      None,
    "match_status":      "unknown",        # confirmed | uncertain | unknown
    "match_confidence":  0.0,
    "dominant_emotion":  "neutral",
    "face_bbox":         None,             # {x,y,width,height,confidence} or None
    "recording":         False,
    "partial_transcript": "",
    "last_updated":      time.time(),
    # Temporary storage for unregistered person
    "pending_embedding": None,
    "needs_registration": False,
}


def _sanitize(obj):
    """
    Recursively convert numpy scalars → native Python types so FastAPI
    can JSON-serialize the session state without errors.
    """
    import numpy as np
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def get_session_state() -> dict:
    """Thread-safe, JSON-safe snapshot of current session state."""
    with _state_lock:
        return _sanitize(dict(session_state))


def _update_state(**kwargs):
    with _state_lock:
        session_state.update(kwargs)
        session_state["last_updated"] = time.time()


# ── Loop control ──────────────────────────────────────────────────────────────
_running = False
_loop_thread: Optional[threading.Thread] = None


def start_session_loop():
    global _running, _loop_thread
    if _running:
        return
    _running = True
    _loop_thread = threading.Thread(target=_main_loop, daemon=True, name="SessionLoop")
    _loop_thread.start()
    print("[SessionLoop] Started ✓")


def stop_session_loop():
    global _running
    _running = False
    print("[SessionLoop] Stop requested")


# ── Main loop ─────────────────────────────────────────────────────────────────

def _main_loop():
    cap = None
    try:
        cap = cv2.VideoCapture(WEBCAM_INDEX)
        if not cap.isOpened():
            print("[SessionLoop] WARNING: Could not open webcam — loop running in headless mode")
            cap = None
    except Exception as e:
        print(f"[SessionLoop] Webcam open error: {e}")
        cap = None

    last_person_time   = 0.0
    session_start_time = 0.0
    in_session         = False

    _update_state(status="detecting")

    while _running:
        frame = _capture_frame(cap)

        if frame is None:
            # Headless / no camera — keep polling
            time.sleep(FRAME_INTERVAL_S)
            continue

        try:
            person_present = detect_person(frame)
        except Exception as e:
            print(f"[SessionLoop] Detection error: {e}")
            time.sleep(FRAME_INTERVAL_S)
            continue

        now = time.time()

        if person_present:
            last_person_time = now
            bbox = get_face_bbox(frame)

            # Face emotion for live display
            try:
                if facial_analyzer:
                    emotion_result = facial_analyzer.analyze_frame(frame)
                    dominant_emotion = emotion_result.dominant_emotion
                else:
                    dominant_emotion = "neutral"
            except Exception:
                dominant_emotion = "neutral"

            if not in_session:
                # ── New session: identify the person ──────────────────────────
                in_session         = True
                session_start_time = now
                print("[SessionLoop] Person detected — starting session")

                embedding = []
                person_id  = None
                person_name     = None
                relationship    = None
                match_status    = "unknown"
                match_confidence = 0.0

                try:
                    face_roi  = crop_face(frame)
                    if face_roi is not None:
                        embedding = generate_embedding(face_roi)
                except Exception as e:
                    print(f"[SessionLoop] Embedding error: {e}")

                if embedding:
                    try:
                        db_encodings = get_all_face_encodings(USER_ID)
                        person_id, match_confidence, match_status = compare_embedding(
                            embedding, db_encodings
                        )
                        if person_id and match_status in ("confirmed", "uncertain"):
                            person_data  = get_known_person(person_id)
                            person_name  = person_data["name"] if person_data else "Unknown"
                            relationship = person_data["relationshiptype"] if person_data else None
                    except Exception as e:
                        print(f"[SessionLoop] Matching error: {e}")

                needs_reg = (match_status == "unknown")
                _update_state(
                    status="active",
                    person_detected=True,
                    person_id=person_id,
                    person_name=person_name,
                    relationship=relationship,
                    match_status=match_status,
                    match_confidence=match_confidence,
                    dominant_emotion=dominant_emotion,
                    face_bbox=bbox,
                    recording=True,
                    needs_registration=needs_reg,
                    pending_embedding=embedding if needs_reg else None,
                )
                record_audio(
                    on_transcript=lambda text: _update_state(partial_transcript=text)
                )

            else:
                # ── Ongoing session: update emotion + bbox ─────────────────────
                _update_state(
                    person_detected=True,
                    dominant_emotion=dominant_emotion,
                    face_bbox=bbox,
                )

        else:
            # ── Person absent ──────────────────────────────────────────────────
            _update_state(person_detected=False, face_bbox=None)

            if in_session and (now - last_person_time) >= ABSENCE_TIMEOUT_S:
                print(f"[SessionLoop] Person absent {ABSENCE_TIMEOUT_S}s — ending session")
                in_session = False
                _update_state(status="saving", recording=False)

                audio_data = stop_recording()
                _save_session_async(audio_data)

        time.sleep(FRAME_INTERVAL_S)

    # Cleanup
    if cap:
        cap.release()
    _update_state(status="idle", person_detected=False, recording=False)
    print("[SessionLoop] Stopped")


def _capture_frame(cap) -> Optional[np.ndarray]:
    if cap is None:
        return None
    try:
        ret, frame = cap.read()
        return frame if ret else None
    except Exception:
        return None


def _save_session_async(audio_data: np.ndarray):
    """Run transcription + DB save in a background thread so the loop isn't blocked."""
    t = threading.Thread(
        target=_save_session,
        args=(audio_data,),
        daemon=True,
    )
    t.start()


def _save_session(audio_data: np.ndarray):
    with _state_lock:
        person_id    = session_state.get("person_id")
        emotion      = session_state.get("dominant_emotion", "neutral")
        # Use the live (chunk-by-chunk) transcript if it already has content
        live_tx      = session_state.get("partial_transcript", "").strip()

    try:
        # Prefer the live VAD transcript; fallback to Whisper on full audio
        if live_tx:
            transcript = live_tx
            print(f"[SessionLoop] Using live transcript ({len(transcript)}c)")
        else:
            transcript = transcribe_audio(audio_data)

        summary = summarize_conversation(transcript)

        interaction_id = save_conversation(
            userid=USER_ID,
            person_id=person_id,
            transcript=transcript,
            summary=summary,
            emotion=emotion,
            location="Living Room",
        )
        save_emotion_record(interaction_id, emotion, 0.80)

        _update_state(
            status="detecting",
            partial_transcript=transcript,   # keep last transcript visible briefly
            person_id=None,
            person_name=None,
            relationship=None,
            match_status="unknown",
            match_confidence=0.0,
            pending_embedding=None,
            needs_registration=False,
        )
        print(f"[SessionLoop] Session saved — interactionid={interaction_id}")

    except Exception as e:
        print(f"[SessionLoop] Save error: {e}")
        _update_state(status="detecting")
