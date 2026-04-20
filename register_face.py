"""
register_face.py
================
Registers YOUR face into the database.
Run once per person before running test_face_recog.py
"""

import cv2
import time
import json
from dotenv import load_dotenv
from app.services.face_recognition.face_service import (
    detect_person,
    crop_face,
    generate_embedding,
)
from app.database.db import get_db_connection

def register_face(person_name: str, relationship: str, priority: int = 3):
    load_dotenv()

    print(f"\n📸 Registering face for: {person_name} ({relationship})")

    # Step 1 — Capture face from webcam
    print("Initializing Webcam... Look at the camera!")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open webcam.")
        return

    time.sleep(2)
    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        print("❌ Failed to capture image.")
        return
    print("✅ Frame captured.")

    # Step 2 — Detect person
    person_detected, bbox = detect_person(frame)
    if not person_detected:
        print("❌ No person detected. Make sure your face is clearly visible and try again.")
        return
    print(f"✅ Person detected. Bounding Box: {bbox}")

    # Step 3 — Crop face
    face_roi = crop_face(frame, bbox)
    if face_roi is None:
        print("❌ Face crop failed.")
        return
    cv2.imwrite("registered_face.jpg", cv2.cvtColor(face_roi, cv2.COLOR_RGB2BGR))
    print("✅ Face cropped. Saved to registered_face.jpg for review.")

    # Step 4 — Generate embedding
    print("Generating 512-d embedding (this takes a moment)...")
    embedding = generate_embedding(face_roi)
    if embedding is None:
        print("❌ Failed to generate embedding.")
        return
    print(f"✅ Generated {len(embedding)}-d embedding.")

    # Step 5 — Save to DB
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Insert into knownperson
        cur.execute(
            """
            INSERT INTO public.knownperson (name, relationshiptype, prioritylevel, notes)
            VALUES (%s, %s, %s, %s)
            RETURNING personid;
            """,
            (person_name, relationship, priority, f"Registered via register_face.py")
        )
        person_id = cur.fetchone()[0]
        print(f"✅ Created person record: personid={person_id}")

        # Insert embedding
        cur.execute(
            """
            INSERT INTO public.faceencoding (personid, encodingdata, confidencescore)
            VALUES (%s, %s, %s)
            RETURNING faceencodingid;
            """,
            (person_id, json.dumps(embedding), 1.0)
        )
        encoding_id = cur.fetchone()[0]
        conn.commit()
        print(f"✅ Saved face embedding: faceencodingid={encoding_id}")
        print(f"\n🎉 Registration complete! You can now run python test_face_recog.py")

    except Exception as e:
        conn.rollback()
        print(f"❌ DB error: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    # ✏️ Change these to YOUR name and relationship
    YOUR_NAME = input("Enter your name: ").strip()
    YOUR_RELATIONSHIP = input("Enter your relationship (e.g. Owner, Family, Friend): ").strip()
    register_face(YOUR_NAME, YOUR_RELATIONSHIP)
