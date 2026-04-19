"""
Face Recognition Service
========================
Implements the five-step pipeline for the AI memory assistant:

    detect_person_yolo()       – YOLOv8 person detection
    crop_face_opencv()         – Face region extraction with OpenCV
    generate_embedding_deepface() – DeepFace embedding vector
    compare_embeddings()       – Cosine similarity against stored embeddings
    fetch_person_details()     – PostgreSQL person + conversation lookup
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import cv2
import numpy as np
from deepface import DeepFace
from ultralytics import YOLO

from app.database.db import get_db_connection

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

YOLO_MODEL_PATH = "yolov8n.pt"          # downloaded automatically on first run
DEEPFACE_MODEL = "Facenet512"           # 512-dim embedding; accurate & fast
DEEPFACE_DETECTOR = "retinaface"        # robust built-in detector
DEEPFACE_ENFORCE_DETECTION = False      # don't crash if face isn't found

CONFIDENCE_CONFIRMED = 0.85             # ≥ 0.85 → confirmed match
CONFIDENCE_UNCERTAIN = 0.70            # 0.70–0.85 → uncertain match
                                        # < 0.70 → unknown person

# YOLO class id for "person" in the COCO dataset
YOLO_PERSON_CLASS_ID = 0

# Minimum YOLO confidence to treat a detection as valid
YOLO_MIN_CONFIDENCE = 0.50

# Padding (px) added around the detected bounding box before cropping
FACE_CROP_PADDING = 20

# ---------------------------------------------------------------------------
# Lazy-load the YOLO model once
# ---------------------------------------------------------------------------

_yolo_model: Optional[YOLO] = None


def _get_yolo_model() -> YOLO:
    global _yolo_model
    if _yolo_model is None:
        logger.info("Loading YOLOv8 model: %s", YOLO_MODEL_PATH)
        _yolo_model = YOLO(YOLO_MODEL_PATH)
    return _yolo_model


# ---------------------------------------------------------------------------
# 1. detect_person_yolo
# ---------------------------------------------------------------------------

def detect_person_yolo(frame: np.ndarray) -> tuple[bool, Optional[tuple[int, int, int, int]]]:
    """
    Run YOLOv8 on *frame* and return the highest-confidence person bounding box.

    Parameters
    ----------
    frame : np.ndarray
        BGR image (as returned by ``cv2.imdecode`` / ``cv2.VideoCapture``).

    Returns
    -------
    (person_detected, bbox)
        ``person_detected`` is True if at least one person was found.
        ``bbox`` is ``(x1, y1, x2, y2)`` in pixel coordinates, or None.
    """
    model = _get_yolo_model()
    results = model(frame, verbose=False)

    best_conf = 0.0
    best_box: Optional[tuple[int, int, int, int]] = None

    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            if cls_id == YOLO_PERSON_CLASS_ID and conf >= YOLO_MIN_CONFIDENCE:
                if conf > best_conf:
                    best_conf = conf
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    best_box = (x1, y1, x2, y2)

    if best_box is None:
        logger.debug("No person detected by YOLO. Trying OpenCV Face Cascade fallback.")
        return detect_face_opencv(frame)

    logger.debug("Person detected with conf=%.3f bbox=%s", best_conf, best_box)
    return True, best_box

# Load Haar cascade once globally
_face_cascade = None

def get_face_cascade():
    global _face_cascade
    if _face_cascade is None:
        _face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    return _face_cascade

def detect_face_opencv(frame: np.ndarray) -> tuple[bool, Optional[tuple[int, int, int, int]]]:
    """Fallback detector using OpenCV Haar Cascade to catch close-up faces."""
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cascade = get_face_cascade()
        # minNeighbors=5, scaleFactor=1.1 are standard robust params
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        
        if len(faces) > 0:
            # Get the largest face
            faces_sorted = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
            x, y, w, h = faces_sorted[0]
            bbox = (x, y, x + w, y + h)
            return True, bbox
    except Exception as e:
        logger.debug(f"OpenCV fallback detection failed: {e}")
        
    return False, None


# ---------------------------------------------------------------------------
# 2. crop_face_opencv
# ---------------------------------------------------------------------------

def crop_face_opencv(
    frame: np.ndarray,
    bbox: tuple[int, int, int, int],
    padding: int = FACE_CROP_PADDING,
) -> Optional[np.ndarray]:
    """
    Crop and preprocess the face region from *frame*.

    The function:
        1. Expands the YOLO bounding box by *padding* pixels on all sides.
        2. Clips to image boundaries.
        3. Converts BGR → RGB (required by DeepFace).
        4. Resizes to 224×224 (standard input for most face models).

    Parameters
    ----------
    frame  : np.ndarray  BGR source image.
    bbox   : (x1, y1, x2, y2) bounding box from YOLO.
    padding: extra pixels to include around the box.

    Returns
    -------
    np.ndarray (RGB, 224×224) or None if the crop area is empty.
    """
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = bbox

    # Add padding and clamp to image borders
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(w, x2 + padding)
    y2 = min(h, y2 + padding)

    if x2 <= x1 or y2 <= y1:
        logger.warning("Degenerate crop region; skipping.")
        return None

    crop = frame[y1:y2, x1:x2]
    crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(crop_rgb, (224, 224), interpolation=cv2.INTER_LINEAR)
    return resized


# ---------------------------------------------------------------------------
# 3. generate_embedding_deepface
# ---------------------------------------------------------------------------

def generate_embedding_deepface(face_image: np.ndarray) -> Optional[list[float]]:
    """
    Generate a face embedding vector using DeepFace.

    Parameters
    ----------
    face_image : np.ndarray
        RGB image (224×224) produced by ``crop_face_opencv``.

    Returns
    -------
    list[float] embedding vector, or None if DeepFace could not find a face.
    """
    try:
        result = DeepFace.represent(
            img_path=face_image,
            model_name=DEEPFACE_MODEL,
            detector_backend=DEEPFACE_DETECTOR,
            enforce_detection=DEEPFACE_ENFORCE_DETECTION,
        )
        if not result:
            logger.warning("DeepFace returned empty result.")
            return None
        embedding: list[float] = result[0]["embedding"]
        logger.debug("Embedding generated, dim=%d", len(embedding))
        return embedding
    except Exception as exc:
        logger.error("DeepFace embedding failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# 4. compare_embeddings
# ---------------------------------------------------------------------------

def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Return cosine similarity in [0, 1] between two 1-D vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def compare_embeddings(
    query_embedding: list[float],
) -> tuple[Optional[int], float]:
    """
    Compare *query_embedding* against every row in ``public.faceencoding``.

    Embeddings are stored as JSON-serialised arrays in the ``encodingdata``
    TEXT column (no pgvector extension required).

    Parameters
    ----------
    query_embedding : list[float]  The embedding produced for the current frame.

    Returns
    -------
    (best_person_id, best_similarity)
        ``best_person_id`` is None when the table is empty.
        ``best_similarity`` is a float in [0, 1].
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT personid, encodingdata FROM public.faceencoding;"
        )
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    if not rows:
        logger.info("faceencoding table is empty – treating as unknown.")
        return None, 0.0

    query_vec = np.array(query_embedding, dtype=np.float32)
    best_person_id: Optional[int] = None
    best_similarity = -1.0

    for personid, encoding_data in rows:
        stored_list: list[float] = (
            json.loads(encoding_data)
            if isinstance(encoding_data, str)
            else encoding_data
        )
        stored_vec = np.array(stored_list, dtype=np.float32)
        sim = _cosine_similarity(query_vec, stored_vec)
        if sim > best_similarity:
            best_similarity = sim
            best_person_id = personid

    logger.debug(
        "Best match: personid=%s  similarity=%.4f", best_person_id, best_similarity
    )
    return best_person_id, best_similarity


# ---------------------------------------------------------------------------
# 5. fetch_person_details
# ---------------------------------------------------------------------------

def fetch_person_details(person_id: int) -> Optional[dict]:
    """
    Fetch person metadata and their most recent conversation from PostgreSQL.

    Queries:
        * ``public.knownperson`` for name, relationship type.
        * ``public.conversation``  for the latest interaction date, summary,
          and emotion detected.

    Returns
    -------
    dict with keys matching the API response schema, or None if not found.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Person basic info
        cur.execute(
            """
            SELECT name, relationshiptype
            FROM   public.knownperson
            WHERE  personid = %s;
            """,
            (person_id,),
        )
        person_row = cur.fetchone()
        if person_row is None:
            logger.warning("personid=%s not found in knownperson.", person_id)
            return None

        name, relationship_type = person_row

        # Latest conversation
        cur.execute(
            """
            SELECT interactiondatetime, summarytext, emotiondetected
            FROM   public.conversation
            WHERE  personid = %s
            ORDER  BY interactiondatetime DESC
            LIMIT  1;
            """,
            (person_id,),
        )
        conv_row = cur.fetchone()

        last_interaction_date = None
        last_summary = None
        last_emotion = None

        if conv_row:
            dt, last_summary, last_emotion = conv_row
            last_interaction_date = dt.strftime("%Y-%m-%d") if dt else None

        return {
            "person_name": name,
            "relationship_type": relationship_type,
            "last_interaction_date": last_interaction_date,
            "last_conversation_summary": last_summary,
            "last_emotion": last_emotion,
        }

    finally:
        cur.close()
        conn.close()
