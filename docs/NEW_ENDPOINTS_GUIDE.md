# New Endpoints Guide - Quick Reference

## What's New?

We've added **17 new endpoints** to cover all database tables. The backend now has complete CRUD operations for users, caregivers, and emotion records.

---

## Quick Start

### 1. User Management

**Create a user**:
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "age": 65,
    "medicalcondition": "Short-term memory loss",
    "emergencycontact": "+1234567890"
  }'
```

**Get user**:
```bash
curl http://localhost:8000/api/users/1
```

**List all users**:
```bash
curl http://localhost:8000/api/users/?skip=0&limit=10
```

**Update user**:
```bash
curl -X PUT http://localhost:8000/api/users/1 \
  -H "Content-Type: application/json" \
  -d '{"age": 66}'
```

**Delete user**:
```bash
curl -X DELETE http://localhost:8000/api/users/1
```

---

### 2. Caregiver Management

**Create a caregiver**:
```bash
curl -X POST http://localhost:8000/api/caregivers/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "relationshiptouser": "daughter",
    "accesslevel": "admin"
  }'
```

**Assign caregiver to user**:
```bash
curl -X POST http://localhost:8000/api/caregivers/assign \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "caregiver_id": 1}'
```

**Get user's caregivers**:
```bash
curl http://localhost:8000/api/users/1/caregivers
```

**Unassign caregiver**:
```bash
curl -X POST http://localhost:8000/api/caregivers/unassign \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "caregiver_id": 1}'
```

---

### 3. Emotion Records

**Record an emotion** (Member A):
```bash
curl -X POST http://localhost:8000/api/emotions/ \
  -H "Content-Type: application/json" \
  -d '{
    "interaction_id": 123,
    "emotiontype": "happy",
    "confidencelevel": 0.85
  }'
```

**Get emotions for an interaction**:
```bash
curl http://localhost:8000/api/emotions/interaction/123
```

**Common emotion types**:
- `happy`
- `sad`
- `angry`
- `neutral`
- `surprised`
- `fearful`

---

## Complete Workflow Example

```bash
# Step 1: Create a user
USER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com", "age": 65}')
USER_ID=$(echo $USER_RESPONSE | jq -r '.userid')

# Step 2: Create a caregiver
CAREGIVER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/caregivers/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Doe", "relationshiptouser": "daughter", "accesslevel": "admin"}')
CAREGIVER_ID=$(echo $CAREGIVER_RESPONSE | jq -r '.caregiverid')

# Step 3: Assign caregiver to user
curl -X POST http://localhost:8000/api/caregivers/assign \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": $USER_ID, \"caregiver_id\": $CAREGIVER_ID}"

# Step 4: Register a person (requires face encoding)
PERSON_RESPONSE=$(curl -s -X POST http://localhost:8000/api/persons/register \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": $USER_ID, \"name\": \"Ravi Kumar\", \"relationship_type\": \"colleague\", \"encoding\": [0.1, 0.2, ...]}")
PERSON_ID=$(echo $PERSON_RESPONSE | jq -r '.person_id')

# Step 5: Start an interaction
INTERACTION_RESPONSE=$(curl -s -X POST http://localhost:8000/api/interactions/start \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": $USER_ID, \"person_id\": $PERSON_ID, \"location\": \"Living Room\"}")
INTERACTION_ID=$(echo $INTERACTION_RESPONSE | jq -r '.interaction_id')

# Step 6: Record emotion during interaction
curl -X POST http://localhost:8000/api/emotions/ \
  -H "Content-Type: application/json" \
  -d "{\"interaction_id\": $INTERACTION_ID, \"emotiontype\": \"happy\", \"confidencelevel\": 0.85}"

# Step 7: Transcribe audio
curl -X POST http://localhost:8000/api/audio/transcribe \
  -F "audio=@recording.wav" \
  -F "interaction_id=$INTERACTION_ID"

# Step 8: End interaction
curl -X POST http://localhost:8000/api/interactions/end \
  -H "Content-Type: application/json" \
  -d "{\"interaction_id\": $INTERACTION_ID}"

# Step 9: View emotions for the interaction
curl http://localhost:8000/api/emotions/interaction/$INTERACTION_ID
```

---

## API Documentation

### Interactive Docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Try It Out
1. Start the server: `cd backend && python run.py`
2. Open http://localhost:8000/docs
3. Click on any endpoint
4. Click "Try it out"
5. Fill in the parameters
6. Click "Execute"

---

## Endpoint Summary

### Users (7 endpoints)
- `POST /api/users/` - Create
- `GET /api/users/{user_id}` - Get by ID
- `GET /api/users/` - List all
- `PUT /api/users/{user_id}` - Update
- `DELETE /api/users/{user_id}` - Delete
- `GET /api/users/{user_id}/caregivers` - Get caregivers
- `GET /api/users/{user_id}/persons` - Get known persons

### Caregivers (7 endpoints)
- `POST /api/caregivers/` - Create
- `GET /api/caregivers/{caregiver_id}` - Get by ID
- `GET /api/caregivers/` - List all
- `PUT /api/caregivers/{caregiver_id}` - Update
- `DELETE /api/caregivers/{caregiver_id}` - Delete
- `POST /api/caregivers/assign` - Assign to user
- `POST /api/caregivers/unassign` - Unassign from user

### Emotions (5 endpoints)
- `POST /api/emotions/` - Create
- `GET /api/emotions/{emotion_id}` - Get by ID
- `GET /api/emotions/interaction/{interaction_id}` - Get for interaction
- `GET /api/emotions/` - List all
- `DELETE /api/emotions/{emotion_id}` - Delete

---

## Common Use Cases

### For Frontend Developers
1. **User Registration**: Use `POST /api/users/`
2. **User Profile**: Use `GET /api/users/{user_id}`
3. **Caregiver Dashboard**: Use `GET /api/users/{user_id}/caregivers`
4. **Emotion Analytics**: Use `GET /api/emotions/interaction/{interaction_id}`

### For Member A (Detection System)
1. **Record Emotions**: Use `POST /api/emotions/` after emotion detection
2. **Create Users**: Use `POST /api/users/` for new users
3. **Register Persons**: Use `POST /api/persons/register` for new faces

### For Admin Panel
1. **Manage Users**: Full CRUD via `/api/users/` endpoints
2. **Manage Caregivers**: Full CRUD via `/api/caregivers/` endpoints
3. **Assign Relationships**: Use `/api/caregivers/assign` and `/unassign`

---

## Error Handling

### Common Errors

**400 Bad Request**:
```json
{
  "detail": "User with email john@example.com already exists"
}
```

**404 Not Found**:
```json
{
  "detail": "User 999 not found"
}
```

**422 Validation Error**:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## Migration from Old System

### Before (No user management)
```python
# Had to manually insert users in database
```

### After (Full user management)
```python
import requests

# Create user via API
response = requests.post(
    "http://localhost:8000/api/users/",
    json={
        "name": "John Doe",
        "email": "john@example.com",
        "age": 65
    }
)
user = response.json()
user_id = user["userid"]
```

---

## Testing

### Unit Tests
```bash
cd backend
pytest tests/
```

### Manual Testing
Use the Swagger UI at http://localhost:8000/docs

### Integration Testing
Run the complete workflow example above

---

## Support

- **API Contracts**: See `docs/API_CONTRACTS.md`
- **Complete Summary**: See `docs/COMPLETE_API_SUMMARY.md`
- **Backend README**: See `docs/BACKEND_README.md`
- **Swagger UI**: http://localhost:8000/docs

---

**Status**: ✅ Ready for integration  
**Version**: 2.0.0  
**Last Updated**: April 19, 2026
