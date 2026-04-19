"""
services/ml/face_recognition_service.py
----------------------------------------
Core face-recognition engine using:
  - OpenCV SSD ResNet (already downloaded) for face detection
  - facenet-pytorch InceptionResnetV1 (pretrained on VGGFace2) for 512-d embeddings

Public helper functions (as specified):
    detect_person(frame)        → bool
    crop_face(frame)            → np.ndarray | None
    get_face_bbox(frame)        → dict | None
    generate_embedding(face_roi)→ list[float]
    compare_embedding(emb, db_records) → (personid|None, float, str)

Confidence thresholds:
    > 0.85  → "confirmed"
    0.70–0.85 → "uncertain"
    < 0.70  → "unknown"
"""

import os
import json
import threading
from typing import Optional

import cv2
import numpy as np
import torch
from torchvision import transforms
from facenet_pytorch import InceptionResnetV1

# ── Confidence thresholds ──────────────────────────────────────────────────────
THRESHOLD_CONFIRMED = 0.85
THRESHOLD_UNCERTAIN = 0.70

# ── DNN model paths (already present in the repo) ─────────────────────────────
_BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.abspath(os.path.join(_BASE_DIR, "..", "..", ".."))
DNN_PROTO    = os.path.join(_BACKEND_DIR, "deploy.prototxt")
DNN_WEIGHTS  = os.path.join(_BACKEND_DIR, "res10_300x300_ssd_iter_140000.caffemodel")
DNN_MIN_CONF = 0.50

# ── FaceNet model ────────────────────────────────────────────────────────────
_model_lock = threading.Lock()
_facenet: Optional[InceptionResnetV1] = None

# ── Preprocessing transform for FaceNet (160×160, normalised) ─────────────────
_transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((160, 160)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
])


def _load_facenet() -> InceptionResnetV1:
    global _facenet
    with _model_lock:
        if _facenet is not None:
            return _facenet
        print("[FaceRecognition] Loading FaceNet (VGGFace2)…")
        _facenet = InceptionResnetV1(pretrained="vggface2").eval()
        print("[FaceRecognition] FaceNet ready ✓")
        return _facenet


# ── Singleton DNN net ─────────────────────────────────────────────────────────
_net_lock = threading.Lock()
_net: Optional[cv2.dnn_Net] = None


def _load_net() -> Optional[cv2.dnn_Net]:
    global _net
    with _net_lock:
        if _net is not None:
            return _net
        if os.path.exists(DNN_PROTO) and os.path.exists(DNN_WEIGHTS):
            try:
                _net = cv2.dnn.readNetFromCaffe(DNN_PROTO, DNN_WEIGHTS)
                print("[FaceRecognition] DNN detector loaded ✓")
            except Exception as e:
                print(f"[FaceRecognition] DNN load failed: {e}")
        else:
            print("[FaceRecognition] DNN files not found; face detection unavailable")
        return _net


def _detect_faces_dnn(frame: np.ndarray) -> list:
    """
    Run SSD ResNet face detector.
    Returns list of (x1, y1, x2, y2, confidence) sorted by area descending.
    """
    net = _load_net()
    if net is None:
        return []

    h, w = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(
        cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0)
    )
    net.setInput(blob)
    detections = net.forward()

    results = []
    for i in range(detections.shape[2]):
        conf = float(detections[0, 0, i, 2])
        if conf < DNN_MIN_CONF:
            continue
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        x1, y1, x2, y2 = box.astype(int)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 > x1 and y2 > y1:
            results.append((x1, y1, x2, y2, conf))

    results.sort(key=lambda r: (r[2] - r[0]) * (r[3] - r[1]), reverse=True)
    return results


# ═════════════════════════════════════════════════════════════════════════════
# Public helper functions
# ═════════════════════════════════════════════════════════════════════════════

def detect_person(frame: np.ndarray) -> bool:
    """Return True if at least one face is detected in the frame."""
    try:
        return len(_detect_faces_dnn(frame)) > 0
    except Exception as e:
        print(f"[FaceRecognition] detect_person error: {e}")
        return False


def crop_face(frame: np.ndarray) -> Optional[np.ndarray]:
    """
    Return the largest detected face as a BGR numpy array (with 10% padding),
    or None if no face found.
    """
    try:
        faces = _detect_faces_dnn(frame)
        if not faces:
            return None
        x1, y1, x2, y2, _ = faces[0]
        pad_x = int((x2 - x1) * 0.10)
        pad_y = int((y2 - y1) * 0.10)
        h, w  = frame.shape[:2]
        return frame[
            max(0, y1 - pad_y): min(h, y2 + pad_y),
            max(0, x1 - pad_x): min(w, x2 + pad_x),
        ]
    except Exception as e:
        print(f"[FaceRecognition] crop_face error: {e}")
        return None


def get_face_bbox(frame: np.ndarray) -> Optional[dict]:
    """Return bounding-box dict for the largest face, for frontend overlay."""
    try:
        faces = _detect_faces_dnn(frame)
        if not faces:
            return None
        x1, y1, x2, y2, conf = faces[0]
        # Cast to native Python ints/float so FastAPI can JSON-serialize them
        return {
            "x":          int(x1),
            "y":          int(y1),
            "width":      int(x2 - x1),
            "height":     int(y2 - y1),
            "confidence": round(float(conf), 3),
        }
    except Exception:
        return None


def generate_embedding(face_roi: np.ndarray) -> list:
    """
    Generate a 512-d FaceNet embedding from a face crop (BGR numpy array).
    Returns [] on failure.
    """
    try:
        model = _load_facenet()
        # BGR → RGB, then apply FaceNet transform
        rgb   = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
        tensor = _transform(rgb).unsqueeze(0)           # (1, 3, 160, 160)
        with torch.no_grad():
            emb = model(tensor)                          # (1, 512)
        return emb.squeeze(0).tolist()
    except Exception as e:
        print(f"[FaceRecognition] generate_embedding error: {e}")
        return []


def _cosine_similarity(a: list, b: list) -> float:
    """Cosine similarity in [0, 1]."""
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


def compare_embedding(
    embedding: list,
    db_records: list,    # [{"personid":int, "encodingdata":str, ...}, ...]
) -> tuple:
    """
    Compare embedding against every stored encoding.

    Returns:
        (best_personid | None, best_score, match_status)

    match_status: "confirmed" | "uncertain" | "unknown"
    """
    if not embedding or not db_records:
        return None, 0.0, "unknown"

    best_pid   = None
    best_score = 0.0

    for record in db_records:
        try:
            stored = json.loads(record["encodingdata"])
        except (json.JSONDecodeError, TypeError, KeyError):
            continue
        if not stored:
            continue
        sim = _cosine_similarity(embedding, stored)
        if sim > best_score:
            best_score = sim
            best_pid   = record["personid"]

    best_score = round(float(best_score), 4)   # ensure native Python float
    best_pid   = int(best_pid) if best_pid is not None else None  # ensure native int

    if best_score > THRESHOLD_CONFIRMED:
        return best_pid, best_score, "confirmed"
    elif best_score > THRESHOLD_UNCERTAIN:
        return best_pid, best_score, "uncertain"
    else:
        return None, best_score, "unknown"
