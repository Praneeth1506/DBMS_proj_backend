"""
Face Controller — FastAPI
=========================
Orchestrates the face recognition pipeline and returns structured JSON.

Exported functions:
    identify_person_from_frame(file)   – UploadFile → full pipeline → JSON
    register_face_embedding(file, personid) – enrol a new face
"""

from __future__ import annotations

import base64
import json
import logging
import os
import tempfile
from typing import Optional

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.services.face_recognition import face_service as fs
from app.database.db import get_db_connection

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _decode_upload(file: UploadFile) -> np.ndarray:
    """Decode an UploadFile into a BGR numpy array via OpenCV."""
    raw = file.file.read()
    arr = np.frombuffer(raw, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Could not decode image file.")
    return frame


def _match_label(confidence: float) -> str:
    if confidence >= fs.THRESHOLD_CONFIRMED:
        return "confirmed"
    if confidence >= fs.THRESHOLD_UNCERTAIN:
        return "uncertain"
    return "unknown"


# ---------------------------------------------------------------------------
# Identify
# ---------------------------------------------------------------------------

async def identify_person_from_frame(file: UploadFile) -> JSONResponse:
    """
    Run the full recognition pipeline on an uploaded webcam frame.

    Pipeline: YOLO detect → OpenCV crop → DeepFace embed → DB compare → fetch details
    """
    frame = _decode_upload(file)

    # Step 1 — Person detection
    person_detected, bbox = fs.detect_person(frame)
    if not person_detected:
        return JSONResponse({
            "person_detected": False,
            "match_status": None,
            "person_name": None,
            "relationship_type": None,
            "confidence": None,
            "last_interaction_date": None,
            "last_conversation_summary": None,
            "last_emotion": None,
        })

    # Step 2 — Crop face
    face_image = fs.crop_face(frame, bbox)
    if face_image is None:
        raise HTTPException(status_code=422, detail="Person detected but face crop failed.")

    # Step 3 — Generate embedding
    embedding = fs.generate_embedding(face_image)
    if embedding is None:
        raise HTTPException(status_code=422, detail="Could not generate face embedding.")

    # Step 4 — Compare embeddings
    best_person_id, similarity, match_status = fs.compare_embedding(embedding)

    # Step 5 — Fetch details
    if match_status == "unknown" or best_person_id is None:
        return JSONResponse({
            "person_detected": True,
            "match_status": "unknown",
            "person_name": "Unknown Person",
            "relationship_type": None,
            "confidence": similarity,
            "last_interaction_date": None,
            "last_conversation_summary": None,
            "last_emotion": None,
        })

    details = fs.fetch_details(best_person_id)
    if details is None:
        return JSONResponse({
            "person_detected": True,
            "match_status": "unknown",
            "person_name": "Unknown Person",
            "relationship_type": None,
            "confidence": similarity,
            "last_interaction_date": None,
            "last_conversation_summary": None,
            "last_emotion": None,
        })

    return JSONResponse({
        "person_detected": True,
        "match_status": match_status,
        "person_name": details["name"],
        "relationship_type": details["relationship"],
        "confidence": similarity,
        "last_interaction_date": details["last_date"],
        "last_conversation_summary": details["last_summary"],
        "last_emotion": details["last_emotion"],
    })


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

async def register_face_embedding(file: UploadFile, personid: int) -> JSONResponse:
    """
    Register a face embedding for an existing knownperson row.
    """
    frame = _decode_upload(file)

    person_detected, bbox = fs.detect_person(frame)
    if not person_detected:
        raise HTTPException(status_code=422, detail="No person detected in the provided frame.")

    face_image = fs.crop_face(frame, bbox)
    if face_image is None:
        raise HTTPException(status_code=422, detail="Face crop failed.")

    embedding = fs.generate_embedding(face_image)
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
        face_encoding_id = row[0] if row else None
    except Exception as exc:
        conn.rollback()
        logger.error("DB insert failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        cur.close()
        conn.close()

    return JSONResponse({
        "message": "Face registered successfully",
        "personid": personid,
        "faceencodingid": face_encoding_id,
    })
