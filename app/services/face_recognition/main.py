import os
import json
import logging

import cv2
import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.services.face_recognition.face_service import (
    detect_person,
    crop_face,
    generate_embedding,
    compare_embedding,
    fetch_details,
)
from app.database.db import get_db_connection, save_conversation

load_dotenv()
logger = logging.getLogger(__name__)

USER_ID = int(os.getenv("USER_ID", "1"))

app = FastAPI(title="Face Recognition Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _decode_frame(file: UploadFile) -> np.ndarray:
    raw = file.file.read()
    arr = np.frombuffer(raw, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image encoding")
    return frame


def _run_pipeline(frame: np.ndarray):
    """
    Smart 2-stage pipeline:
    1. YOLO detect → crop face → embed
    2. Fallback: embed full image directly (handles close-up / pre-cropped photos)
    Returns (embedding, used_fallback)
    """
    detected, bbox = detect_person(frame)

    if detected:
        roi = crop_face(frame, bbox)
        if roi is not None:
            embedding = generate_embedding(roi)
            if embedding:
                return embedding, False

    # Fallback: pass full image to DeepFace
    logger.info("No person via YOLO/Haar — trying direct embedding on full image")
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(img_rgb, (224, 224))
    embedding = generate_embedding(resized)
    return embedding, True


def _log_interaction(person_id: int, summary: str = "", emotion: str = "Neutral") -> int | None:
    """Save a face-detection interaction record to public.conversation with a 5-minute cooldown."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check for last interaction time for this person
        cur.execute(
            """
            SELECT interactiondatetime FROM public.conversation 
            WHERE personid = %s 
            ORDER BY interactiondatetime DESC LIMIT 1
            """,
            (person_id,)
        )
        row = cur.fetchone()
        
        if row:
            from datetime import datetime, timezone
            last_time = row[0]
            # Ensure last_time is offset-aware for comparison
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=timezone.utc)
            
            diff = (datetime.now(timezone.utc) - last_time).total_seconds()
            if diff < 300:  # 5 minutes = 300 seconds
                logger.info(f"Cooldown active for person {person_id} ({int(diff)}s ago). Skipping log.")
                return None

        cur.close()
        conn.close()

        # No recent interaction, save new one
        interaction_id = save_conversation(
            userid=USER_ID,
            personid=person_id,
            transcribed_text="[Face detected via camera]",
            summarized_text=summary or "Person recognized by face recognition system.",
            detected_emotion=emotion,
            location="Living Room",
        )
        logger.info(f"Logged interaction {interaction_id} for person {person_id}")
        return interaction_id
    except Exception as e:
        logger.error(f"Failed to log interaction: {e}")
        return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/identify")
async def identify(file: UploadFile = File(...)):
    """
    Identify a person from a webcam frame.
    - Confirmed match  → returns details + logs to DB
    - Uncertain match  → returns details (no log)
    - Unknown          → returns unknown status
    """
    frame = _decode_frame(file)
    embedding, used_fallback = _run_pipeline(frame)

    if embedding is None:
        return JSONResponse({
            "person_detected": False,
            "match_status": "embedding_failed",
            "message": "Could not generate face embedding from this image.",
        })

    pid, score, status = compare_embedding(embedding)

    response = {
        "person_detected": True,
        "match_status": status,
        "confidence": score,
        "used_fallback_detection": used_fallback,
    }

    if pid and status in ("confirmed", "uncertain"):
        details = fetch_details(pid)
        if details:
            response.update({
                "person_name":  details["name"],
                "relationship": details["relationship"],
                "last_visit":   details["last_date"],
                "last_summary": details["last_summary"],
                "last_emotion": details["last_emotion"],
            })
        # ✅ Log to DB for both confirmed and uncertain
        interaction_id = _log_interaction(pid)
        response["interaction_logged"] = interaction_id is not None
        response["interaction_id"] = interaction_id
        print(f"[FACE] {status.upper()} — {details['name'] if details else pid} | score={score:.4f} | interaction_id={interaction_id}")

    else:
        response["message"] = f"Unknown person. Highest score: {score:.4f}"
        response["interaction_logged"] = False

    return JSONResponse(response)


@app.post("/register")
async def register(
    file: UploadFile = File(...),
    personid: int = Form(..., description="ID in public.knownperson"),
):
    """Register a face embedding for an existing person."""
    frame = _decode_frame(file)
    embedding, _ = _run_pipeline(frame)

    if embedding is None:
        raise HTTPException(status_code=422, detail="Could not generate face embedding.")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO public.faceencoding (personid, encodingdata, confidencescore)
            VALUES (%s, %s, %s)
            RETURNING faceencodingid;
            """,
            (personid, json.dumps(embedding), 1.0),
        )
        row = cur.fetchone()
        conn.commit()
        return JSONResponse({
            "message": "Face registered successfully",
            "personid": personid,
            "faceencodingid": row[0] if row else None,
        })
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        cur.close()
        conn.close()


@app.post("/register-new")
async def register_new(
    file: UploadFile = File(...),
    name: str = Form(...),
    relationship: str = Form(...),
    priority: int = Form(3),
):
    """
    Register a brand-new person: creates knownperson record + saves face embedding.
    Use this when an unknown person is detected via camera.
    """
    frame = _decode_frame(file)
    embedding, _ = _run_pipeline(frame)

    if embedding is None:
        raise HTTPException(status_code=422, detail="Could not generate face embedding from image.")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 1. Create person
        cur.execute(
            """
            INSERT INTO public.knownperson (name, relationshiptype, prioritylevel, notes)
            VALUES (%s, %s, %s, %s)
            RETURNING personid;
            """,
            (name, relationship, priority, "Registered via live camera"),
        )
        person_id = cur.fetchone()[0]

        # 2. Save face embedding
        cur.execute(
            """
            INSERT INTO public.faceencoding (personid, encodingdata, confidencescore)
            VALUES (%s, %s, %s)
            RETURNING faceencodingid;
            """,
            (person_id, json.dumps(embedding), 1.0),
        )
        encoding_id = cur.fetchone()[0]
        conn.commit()

        print(f"[REGISTER] New person: {name} ({relationship}) | personid={person_id}")
        return JSONResponse({
            "message": f"{name} registered successfully.",
            "personid": person_id,
            "faceencodingid": encoding_id,
        })
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        cur.close()
        conn.close()



def health():
    return {"status": "healthy", "service": "face_recognition", "user_id": USER_ID}
