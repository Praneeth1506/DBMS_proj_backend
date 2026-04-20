"""
test_api.py - Comprehensive API testing script
Tests all endpoints and verifies database operations
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_test(test_name, success, response=None):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if not success and response:
        print(f"   Error: {response.text if hasattr(response, 'text') else response}")
    print()

def test_health_check():
    """Test health check endpoint"""
    print("=" * 60)
    print("1. TESTING HEALTH CHECK")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        success = response.status_code == 200
        print_test("GET /health", success, response)
        if success:
            print(f"   Response: {response.json()}")
        return success
    except Exception as e:
        print_test("GET /health", False, str(e))
        return False

def test_user_management():
    """Test user CRUD operations"""
    print("=" * 60)
    print("2. TESTING USER MANAGEMENT")
    print("=" * 60)
    
    # Create user
    user_data = {
        "name": "Test User",
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "age": 65,
        "medicalcondition": "Short-term memory loss",
        "emergencycontact": "+1234567890"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/users/", json=user_data)
        success = response.status_code == 201
        print_test("POST /api/users/ (Create)", success, response)
        
        if not success:
            return None
        
        user = response.json()
        user_id = user["userid"]
        print(f"   Created user ID: {user_id}")
        
        # Get user
        response = requests.get(f"{BASE_URL}/api/users/{user_id}")
        success = response.status_code == 200
        print_test(f"GET /api/users/{user_id} (Read)", success, response)
        
        # List users
        response = requests.get(f"{BASE_URL}/api/users/?skip=0&limit=10")
        success = response.status_code == 200
        print_test("GET /api/users/ (List)", success, response)
        if success:
            print(f"   Total users: {response.json()['total']}")
        
        # Update user
        update_data = {"age": 66}
        response = requests.put(f"{BASE_URL}/api/users/{user_id}", json=update_data)
        success = response.status_code == 200
        print_test(f"PUT /api/users/{user_id} (Update)", success, response)
        
        return user_id
        
    except Exception as e:
        print_test("User Management", False, str(e))
        return None

def test_caregiver_management(user_id):
    """Test caregiver CRUD operations"""
    print("=" * 60)
    print("3. TESTING CAREGIVER MANAGEMENT")
    print("=" * 60)
    
    # Create caregiver
    caregiver_data = {
        "name": "Test Caregiver",
        "relationshiptouser": "daughter",
        "accesslevel": "admin"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/caregivers/", json=caregiver_data)
        success = response.status_code == 201
        print_test("POST /api/caregivers/ (Create)", success, response)
        
        if not success:
            return None
        
        caregiver = response.json()
        caregiver_id = caregiver["caregiverid"]
        print(f"   Created caregiver ID: {caregiver_id}")
        
        # Get caregiver
        response = requests.get(f"{BASE_URL}/api/caregivers/{caregiver_id}")
        success = response.status_code == 200
        print_test(f"GET /api/caregivers/{caregiver_id} (Read)", success, response)
        
        # List caregivers
        response = requests.get(f"{BASE_URL}/api/caregivers/?skip=0&limit=10")
        success = response.status_code == 200
        print_test("GET /api/caregivers/ (List)", success, response)
        if success:
            print(f"   Total caregivers: {response.json()['total']}")
        
        # Assign caregiver to user
        if user_id:
            assign_data = {"user_id": user_id, "caregiver_id": caregiver_id}
            response = requests.post(f"{BASE_URL}/api/caregivers/assign", json=assign_data)
            success = response.status_code == 200
            print_test("POST /api/caregivers/assign (Assign)", success, response)
            
            # Get user's caregivers
            response = requests.get(f"{BASE_URL}/api/users/{user_id}/caregivers")
            success = response.status_code == 200
            print_test(f"GET /api/users/{user_id}/caregivers", success, response)
            if success:
                print(f"   User has {len(response.json())} caregiver(s)")
        
        return caregiver_id
        
    except Exception as e:
        print_test("Caregiver Management", False, str(e))
        return None

def test_person_management(user_id):
    """Test person registration"""
    print("=" * 60)
    print("4. TESTING PERSON MANAGEMENT")
    print("=" * 60)
    
    # Register person with dummy encoding
    person_data = {
        "user_id": user_id,
        "name": "Test Person",
        "relationship_type": "colleague",
        "priority_level": 3,
        "encoding": [0.1] * 128,  # Dummy 128-dimensional encoding
        "confidence_score": 0.95
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/persons/register", json=person_data)
        success = response.status_code == 201
        print_test("POST /api/persons/register", success, response)
        
        if not success:
            return None
        
        person = response.json()
        person_id = person["person_id"]
        print(f"   Registered person ID: {person_id}")
        
        # Identify person (should match)
        identify_data = {
            "user_id": user_id,
            "encoding": [0.1] * 128  # Same encoding
        }
        response = requests.post(f"{BASE_URL}/api/persons/identify", json=identify_data)
        success = response.status_code == 200
        print_test("POST /api/persons/identify", success, response)
        if success:
            result = response.json()
            print(f"   Identified: {result.get('name')} (confidence: {result.get('confidence')})")
        
        return person_id
        
    except Exception as e:
        print_test("Person Management", False, str(e))
        return None

def test_interaction_flow(user_id, person_id):
    """Test interaction start/end flow"""
    print("=" * 60)
    print("5. TESTING INTERACTION FLOW")
    print("=" * 60)
    
    # Start interaction
    interaction_data = {
        "user_id": user_id,
        "person_id": person_id,
        "location": "Living Room"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/interactions/start", json=interaction_data)
        success = response.status_code == 201
        print_test("POST /api/interactions/start", success, response)
        
        if not success:
            return None
        
        interaction = response.json()
        interaction_id = interaction["interaction_id"]
        print(f"   Started interaction ID: {interaction_id}")
        
        # Append transcript
        transcript_data = {
            "interaction_id": interaction_id,
            "transcript_chunk": "Hello, how are you today?"
        }
        response = requests.post(f"{BASE_URL}/api/sessions/append", json=transcript_data)
        success = response.status_code == 200
        print_test("POST /api/sessions/append", success, response)
        
        return interaction_id
        
    except Exception as e:
        print_test("Interaction Flow", False, str(e))
        return None

def test_emotion_records(interaction_id):
    """Test emotion record creation"""
    print("=" * 60)
    print("6. TESTING EMOTION RECORDS")
    print("=" * 60)
    
    # Create emotion record
    emotion_data = {
        "interaction_id": interaction_id,
        "emotiontype": "happy",
        "confidencelevel": 0.85
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/emotions/", json=emotion_data)
        success = response.status_code == 201
        print_test("POST /api/emotions/ (Create)", success, response)
        
        if not success:
            return None
        
        emotion = response.json()
        emotion_id = emotion["emotionid"]
        print(f"   Created emotion ID: {emotion_id}")
        
        # Get emotion
        response = requests.get(f"{BASE_URL}/api/emotions/{emotion_id}")
        success = response.status_code == 200
        print_test(f"GET /api/emotions/{emotion_id} (Read)", success, response)
        
        # Get emotions for interaction
        response = requests.get(f"{BASE_URL}/api/emotions/interaction/{interaction_id}")
        success = response.status_code == 200
        print_test(f"GET /api/emotions/interaction/{interaction_id}", success, response)
        if success:
            print(f"   Interaction has {len(response.json())} emotion(s)")
        
        # List emotions
        response = requests.get(f"{BASE_URL}/api/emotions/?skip=0&limit=10")
        success = response.status_code == 200
        print_test("GET /api/emotions/ (List)", success, response)
        
        return emotion_id
        
    except Exception as e:
        print_test("Emotion Records", False, str(e))
        return None

def test_memory_retrieval(person_id, user_id):
    """Test memory retrieval"""
    print("=" * 60)
    print("7. TESTING MEMORY RETRIEVAL")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/memory/{person_id}?user_id={user_id}")
        success = response.status_code == 200
        print_test(f"GET /api/memory/{person_id}", success, response)
        if success:
            memories = response.json()
            print(f"   Retrieved {len(memories.get('summaries', []))} memory/memories")
        
        return success
        
    except Exception as e:
        print_test("Memory Retrieval", False, str(e))
        return False

def test_cleanup(user_id, caregiver_id):
    """Clean up test data"""
    print("=" * 60)
    print("8. CLEANUP TEST DATA")
    print("=" * 60)
    
    try:
        # Delete user (cascades to interactions, etc.)
        if user_id:
            response = requests.delete(f"{BASE_URL}/api/users/{user_id}")
            success = response.status_code == 204
            print_test(f"DELETE /api/users/{user_id}", success, response)
        
        # Delete caregiver
        if caregiver_id:
            response = requests.delete(f"{BASE_URL}/api/caregivers/{caregiver_id}")
            success = response.status_code == 204
            print_test(f"DELETE /api/caregivers/{caregiver_id}", success, response)
        
        return True
        
    except Exception as e:
        print_test("Cleanup", False, str(e))
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("COGNITIVE MEMORY ASSISTANT - API TEST SUITE")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print("=" * 60 + "\n")
    
    # Test health check
    if not test_health_check():
        print("\n❌ Server is not running or not healthy!")
        print("Please start the server with: cd backend && python run.py")
        return
    
    # Test user management
    user_id = test_user_management()
    if not user_id:
        print("\n❌ User management tests failed!")
        return
    
    # Test caregiver management
    caregiver_id = test_caregiver_management(user_id)
    
    # Test person management
    person_id = test_person_management(user_id)
    if not person_id:
        print("\n❌ Person management tests failed!")
        test_cleanup(user_id, caregiver_id)
        return
    
    # Test interaction flow
    interaction_id = test_interaction_flow(user_id, person_id)
    if not interaction_id:
        print("\n❌ Interaction flow tests failed!")
        test_cleanup(user_id, caregiver_id)
        return
    
    # Test emotion records
    test_emotion_records(interaction_id)
    
    # Test memory retrieval
    test_memory_retrieval(person_id, user_id)
    
    # Cleanup
    test_cleanup(user_id, caregiver_id)
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 60)
    print("\nCheck the results above for any failures.")
    print("All data has been cleaned up from the database.\n")

if __name__ == "__main__":
    main()
