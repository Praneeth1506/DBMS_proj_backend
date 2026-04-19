from fastapi import APIRouter, UploadFile, File, Form
from app.controllers.face_controller import identify_person_from_frame, register_face_embedding

face_router = APIRouter(prefix="/api/face", tags=["Face Recognition"])


@face_router.post("/identify")
async def face_identify(
    frame: UploadFile = File(..., description="Webcam frame image (JPEG/PNG)"),
):
    """
    Identify a person from a webcam frame.

    Runs the full pipeline:
    1. YOLOv8 person detection
    2. OpenCV face crop
    3. DeepFace embedding (Facenet512)
    4. Cosine similarity against stored embeddings
    5. Fetch person details from DB

    **Confidence thresholds:**
    - ≥ 0.85 → `confirmed`
    - 0.70–0.85 → `uncertain`
    - < 0.70 → `unknown`
    """
    return await identify_person_from_frame(file=frame)


@face_router.post("/register")
async def face_register(
    frame: UploadFile = File(..., description="Clear front-facing photo (JPEG/PNG)"),
    personid: int = Form(..., description="ID of the person in public.knownperson"),
):
    """
    Register a face embedding for an existing person.

    Must be called at least once per person before `/identify` can recognise them.
    """
    return await register_face_embedding(file=frame, personid=personid)
