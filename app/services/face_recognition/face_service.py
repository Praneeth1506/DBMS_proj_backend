"""
Face Recognition Service
========================
Unified service for face detection and identification.
Uses YOLOv8 for person detection and DeepFace for embeddings.
"""

import os
import json
import logging
from typing import Optional, Tuple, List

import cv2
import numpy as np
from deepface import DeepFace
from ultralytics import YOLO

from app.database.db import get_db_connection

logger = logging.getLogger(__name__)

# --- Configuration ---
YOLO_MODEL_PATH = "yolov8n.pt"
DEEPFACE_MODEL = "Facenet512"
DEEPFACE_DETECTOR = "retinaface"
DEEPFACE_ENFORCE_DETECTION = False

THRESHOLD_CONFIRMED = 0.70   # auto-confirm above this
THRESHOLD_UNCERTAIN = 0.45   # treat as match above this too (was 0.55)


# --- State ---
_yolo_model: Optional[YOLO] = None
_face_cascade = None

def _get_yolo_model() -> YOLO:
    global _yolo_model
    if _yolo_model is None:
        logger.info("Loading YOLOv8: %s", YOLO_MODEL_PATH)
        _yolo_model = YOLO(YOLO_MODEL_PATH)
    return _yolo_model

def get_face_cascade():
    global _face_cascade
    if _face_cascade is None:
        # Try OpenCV built-in path first
        path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        _face_cascade = cv2.CascadeClassifier(path)
        # Fallback: use the one in project root
        if _face_cascade.empty():
            import os
            root_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'haarcascade_frontalface_default.xml')
            root_path = os.path.abspath(root_path)
            logger.warning(f"Built-in cascade empty, trying project root: {root_path}")
            _face_cascade = cv2.CascadeClassifier(root_path)
        if _face_cascade.empty():
            logger.error("Failed to load Haar Cascade from any path. Fallback detection disabled.")
    return _face_cascade

# --- Core Logic ---

def detect_person(frame: np.ndarray) -> tuple[bool, Optional[tuple[int, int, int, int]]]:
    """Detect person using YOLO or fallback to Haar Cascade."""
    model = _get_yolo_model()
    results = model(frame, verbose=False)
    
    best_box = None
    best_conf = 0.0
    
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            if cls_id == 0 and conf >= 0.50: # 0 is person
                if conf > best_conf:
                    best_conf = conf
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    best_box = (x1, y1, x2, y2)
    
    if best_box:
        return True, best_box
        
    # Fallback — only if Haar Cascade loaded successfully
    cascade = get_face_cascade()
    if cascade is not None and not cascade.empty():
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
        if len(faces) > 0:
            faces = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
            x, y, w, h = faces[0]
            return True, (x, y, x+w, y+h)

    return False, None

def crop_face(frame: np.ndarray, bbox: tuple[int, int, int, int], padding: int = 20) -> Optional[np.ndarray]:
    """Expand bbox and crop face, converting to RGB for DeepFace."""
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = bbox
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(w, x2 + padding)
    y2 = min(h, y2 + padding)
    
    if x2 <= x1 or y2 <= y1: return None
    
    crop = frame[y1:y2, x1:x2]
    crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    return cv2.resize(crop_rgb, (224, 224))

def generate_embedding(face_image: np.ndarray) -> Optional[List[float]]:
    """Generate 512-d embedding using DeepFace."""
    try:
        result = DeepFace.represent(
            img_path=face_image,
            model_name=DEEPFACE_MODEL,
            detector_backend=DEEPFACE_DETECTOR,
            enforce_detection=DEEPFACE_ENFORCE_DETECTION
        )
        return result[0]["embedding"] if result else None
    except Exception as e:
        logger.error(f"DeepFace error: {e}")
        return None

def compare_embedding(embedding: List[float]) -> tuple[Optional[int], float, str]:
    """Compare embedding against database and return (person_id, confidence, status)."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT personid, encodingdata FROM public.faceencoding")
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    if not rows: return None, 0.0, "unknown"

    query_vec = np.array(embedding, dtype=np.float32)
    best_pid, best_sim = None, -1.0
    skipped = 0
    
    for pid, data in rows:
        stored_vec = np.array(json.loads(data) if isinstance(data, str) else data, dtype=np.float32)
        if stored_vec.shape != query_vec.shape:
            skipped += 1
            continue  # Skip dimension-mismatched rows gracefully
        norm_q = np.linalg.norm(query_vec)
        norm_s = np.linalg.norm(stored_vec)
        if norm_q == 0 or norm_s == 0: sim = 0.0
        else: sim = float(np.dot(query_vec, stored_vec) / (norm_q * norm_s))
        
        if sim > best_sim:
            best_sim, best_pid = sim, pid
    
    if skipped:
        logger.warning(f"Skipped {skipped} face encoding(s) with mismatched dimensions.")

    status = "unknown"
    if best_sim >= THRESHOLD_CONFIRMED: status = "confirmed"
    elif best_sim >= THRESHOLD_UNCERTAIN: status = "uncertain"
    
    return best_pid, round(best_sim, 4), status

def fetch_details(person_id: int) -> Optional[dict]:
    """Fetch person name, relationship and latest interaction."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT name, relationshiptype FROM public.knownperson WHERE personid = %s", (person_id,))
        p = cur.fetchone()
        if not p: return None
        
        cur.execute("""
            SELECT interactiondatetime, summarytext, emotiondetected 
            FROM public.conversation WHERE personid = %s 
            ORDER BY interactiondatetime DESC LIMIT 1
        """, (person_id,))
        c = cur.fetchone()
        
        return {
            "name": p[0],
            "relationship": p[1],
            "last_date": c[0].strftime("%Y-%m-%d") if c and c[0] else None,
            "last_summary": c[1] if c else None,
            "last_emotion": c[2] if c else None
        }
    finally:
        cur.close()
        conn.close()
