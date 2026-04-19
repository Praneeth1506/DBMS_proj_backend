import cv2
import time
from app.services.face_recognition.face_recognition_service import (
    detect_person,
    crop_face,
    generate_embedding,
    compare_embedding,
    get_face_bbox
)
from app.services.face_recognition.conversation_service import (
    get_all_face_encodings,
    get_known_person
)

def test_pipeline():
    print("Initializing Webcam...")
    cap = cv2.VideoCapture(0)
    
    # Wait a bit for the camera to warm up
    time.sleep(2)
    
    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        print("❌ Failed to capture image from webcam.")
        return

    print("✅ Successfully captured frame from webcam.")
    
    # 1. Test Detection
    print("\n--- 1. Testing Detection ---")
    person_present = detect_person(frame)
    if person_present:
        print("✅ Person detected in frame!")
        bbox = get_face_bbox(frame)
        print(f"Bounding Box: {bbox}")
    else:
        print("❌ No person detected in frame. Make sure you are visible!")
        return

    # 2. Test Cropping
    print("\n--- 2. Testing Face Cropping ---")
    face_roi = crop_face(frame)
    if face_roi is not None:
        print(f"✅ Face cropped successfully! Shape: {face_roi.shape}")
    else:
        print("❌ Failed to crop face.")
        return

    # 3. Test Embedding
    print("\n--- 3. Testing Face Embedding (FaceNet) ---")
    embedding = generate_embedding(face_roi)
    if embedding:
        print(f"✅ Generated 512-d embedding successfully!")
    else:
        print("❌ Failed to generate embedding.")
        return

    # 4. Test Database Matching
    print("\n--- 4. Testing Database Matching ---")
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    # We use User ID 1 for testing
    user_id = int(os.getenv("USER_ID", "1"))
    print(f"Fetching known encodings for User ID: {user_id}...")
    
    try:
        db_encodings = get_all_face_encodings(user_id)
        print(f"Found {len(db_encodings)} saved encodings in the database.")
        
        person_id, match_score, match_status = compare_embedding(embedding, db_encodings)
        
        if match_status == "confirmed":
            person_data = get_known_person(person_id)
            print(f"✅ EXACT MATCH FOUND! (Score: {match_score:.4f})")
            print(f"➡️  Name: {person_data['name']}")
            print(f"➡️  Relationship: {person_data['relationshiptype']}")
            print(f"➡️  Priority: {person_data['prioritylevel']}")
            
        elif match_status == "uncertain":
            person_data = get_known_person(person_id)
            print(f"⚠️  UNCERTAIN MATCH. (Score: {match_score:.4f})")
            print(f"Looks like it might be: {person_data['name']}")
            
        else:
            print(f"🛑 UNKNOWN PERSON. No strong match found in database. (Highest Score: {match_score:.4f})")
            
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    test_pipeline()
