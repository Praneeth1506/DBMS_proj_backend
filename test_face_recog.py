"""
test_face_recog.py
==================
Smart face pipeline:
- If person is found in DB → show their details
- If unknown → prompt to register them
"""

import cv2
import time
import json
from dotenv import load_dotenv
from app.services.face_recognition.face_service import (
    detect_person,
    crop_face,
    generate_embedding,
    compare_embedding,
    fetch_details,
)
from app.database.db import get_db_connection

load_dotenv()


def capture_frame():
    print("📷 Opening webcam... Look at the camera!")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open webcam.")
        return None
    time.sleep(2)
    ret, frame = cap.read()
    cap.release()
    if not ret or frame is None:
        print("❌ Failed to capture frame.")
        return None
    print("✅ Frame captured.")
    return frame


def register_new_person(embedding):
    print("\n🆕 This person is not in the database.")
    name = input("   Enter their name: ").strip()
    relationship = input("   Enter relationship (e.g. Family, Friend, Colleague): ").strip()
    priority = input("   Priority level 1-5 (default 3): ").strip() or "3"

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO public.knownperson (name, relationshiptype, prioritylevel, notes)
            VALUES (%s, %s, %s, %s)
            RETURNING personid;
            """,
            (name, relationship, int(priority), "Registered via face recognition pipeline")
        )
        person_id = cur.fetchone()[0]

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

        print(f"\n🎉 Registered successfully!")
        print(f"   Name          : {name}")
        print(f"   Relationship  : {relationship}")
        print(f"   Person ID     : {person_id}")
        print(f"   Encoding ID   : {encoding_id}")

    except Exception as e:
        conn.rollback()
        print(f"❌ DB error during registration: {e}")
    finally:
        cur.close()
        conn.close()


def run():
    # 1. Capture
    frame = capture_frame()
    if frame is None:
        return

    # 2. Detect person
    print("\n--- Detecting Person ---")
    person_detected, bbox = detect_person(frame)
    if not person_detected:
        print("❌ No person detected. Make sure your face is clearly visible.")
        return
    print(f"✅ Person detected. BBox: {bbox}")

    # 3. Crop face
    face_roi = crop_face(frame, bbox)
    if face_roi is None:
        print("❌ Could not crop face region.")
        return
    cv2.imwrite("last_detected.jpg", cv2.cvtColor(face_roi, cv2.COLOR_RGB2BGR))
    print("✅ Face cropped. Saved to last_detected.jpg")

    # 4. Generate embedding
    print("\n--- Generating Embedding ---")
    embedding = generate_embedding(face_roi)
    if embedding is None:
        print("❌ Failed to generate face embedding.")
        return
    print(f"✅ Generated {len(embedding)}-d embedding.")

    # 5. Match against DB
    print("\n--- Checking Database ---")
    person_id, score, status = compare_embedding(embedding)

    if status == "confirmed":
        details = fetch_details(person_id)
        print(f"\n✅ KNOWN PERSON (Score: {score:.4f})")
        print(f"   Name          : {details['name']}")
        print(f"   Relationship  : {details['relationship']}")
        print(f"   Last Visit    : {details['last_date'] or 'No previous visit'}")
        print(f"   Last Summary  : {details['last_summary'] or 'None'}")
        print(f"   Last Emotion  : {details['last_emotion'] or 'None'}")

    elif status == "uncertain":
        details = fetch_details(person_id)
        print(f"\n⚠️  POSSIBLE MATCH (Score: {score:.4f}) — needs confirmation")
        print(f"   Might be      : {details['name']}")
        print(f"   Relationship  : {details['relationship']}")
        ans = input("\n   Is this correct? (y/n): ").strip().lower()
        if ans != 'y':
            register_new_person(embedding)

    else:
        print(f"🛑 UNKNOWN PERSON (Highest Score: {score:.4f})")
        ans = input("   Would you like to register this person? (y/n): ").strip().lower()
        if ans == 'y':
            register_new_person(embedding)
        else:
            print("   Skipped registration.")


if __name__ == "__main__":
    run()
