# API Contracts - Team Integration Guide

**CRITICAL**: Share this document with the entire team before anyone writes a single line of integration code. Every hour spent aligning here saves a day of debugging.

## Base URL

```
http://localhost:8000
```

## Authentication

V1 does not implement authentication. All endpoints are publicly accessible.

---

## 1. Person Identification

### `POST /api/persons/identify`

**Called By**: Member A (Frontend/Detection)

**Purpose**: Identify a person by face encoding and retrieve memory context

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "user_id": 1,
  "encoding": [0.123, 0.456, 0.789, ...],  // 128 or 512 floats
  "frame_timestamp": "2026-04-19T10:30:00Z"  // Optional
}
```

**Request Schema**:
- `user_id` (integer, required): User ID (positive integer)
- `encoding` (array of floats, required): Face encoding vector (exactly 128 or 512 dimensions)
- `frame_timestamp` (datetime, optional): Timestamp of the frame

**Response - Person Found (200 OK)**:
```json
{
  "person_id": 42,
  "name": "Ravi Kumar",
  "relationship_type": "colleague",
  "priority_level": 3,
  "confidence": 0.87,
  "memory_context": [
    {
      "date": "2026-04-15T14:30:00Z",
      "summary": "Discussed hospital visit. Ravi seemed anxious. You promised to call him."
    },
    {
      "date": "2026-04-10T09:15:00Z",
      "summary": "Talked about work project deadlines. Ravi mentioned his daughter's graduation."
    }
  ]
}
```

**Response - No Match (200 OK)**:
```json
{
  "person_id": null,
  "name": null,
  "relationship_type": null,
  "priority_level": null,
  "confidence": null,
  "memory_context": []
}
```

**Response Schema**:
- `person_id` (integer | null): Matched person ID, null if no match
- `name` (string | null): Person's name
- `relationship_type` (string | null): Relationship type (e.g., "family", "friend", "colleague")
- `priority_level` (integer | null): Priority level (1-5)
- `confidence` (float | null): Cosine similarity score (0.0-1.0)
- `memory_context` (array): Last 3 interaction summaries
  - `date` (datetime): Interaction date
  - `summary` (string): Interaction summary text

**Error Responses**:
- `400 Bad Request`: Invalid encoding dimensions or missing required fields
- `422 Unprocessable Entity`: Validation error (Pydantic)
- `500 Internal Server Error`: Server error

**Performance Target**: < 500ms

**Notes**:
- Cosine similarity threshold: 0.6 (configurable)
- Returns null person_id if confidence < 0.6
- Memory context is DB-only (no LLM calls)
- Encoding must be exactly 128 or 512 floats

---

## 2. Person Registration

### `POST /api/persons/register`

**Called By**: Member A (Frontend/Detection)

**Purpose**: Register a new unknown person with face encoding

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "user_id": 1,
  "name": "John Doe",
  "relationship_type": "friend",
  "priority_level": 3,
  "encoding": [0.123, 0.456, 0.789, ...],  // 128 or 512 floats
  "confidence_score": 0.95
}
```

**Request Schema**:
- `user_id` (integer, required): User ID (positive integer)
- `name` (string, required): Person's name (1-100 characters)
- `relationship_type` (string, optional): Relationship type (max 50 characters)
- `priority_level` (integer, optional): Priority level (1-5)
- `encoding` (array of floats, required): Face encoding vector (exactly 128 or 512 dimensions)
- `confidence_score` (float, optional): Confidence score from face detection (0.0-1.0)

**Response (201 Created)**:
```json
{
  "person_id": 43,
  "message": "Person registered successfully"
}
```

**Response Schema**:
- `person_id` (integer): Newly created person ID
- `message` (string): Success message

**Error Responses**:
- `400 Bad Request`: Invalid encoding dimensions or missing required fields
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

**Performance Target**: < 300ms

**Notes**:
- Creates person in `knownperson` table
- Stores face encoding in `faceencoding` table as JSON text
- Links person to user via `userknownperson` junction table

---

## 3. Interaction Start

### `POST /api/interactions/start`

**Called By**: Member A (Frontend/Detection)

**Purpose**: Start a new interaction when a person is detected

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "user_id": 1,
  "person_id": 42,
  "location": "Living Room"  // Optional
}
```

**Request Schema**:
- `user_id` (integer, required): User ID (positive integer)
- `person_id` (integer, required): Person ID (positive integer)
- `location` (string, optional): Location string (max 100 characters)

**Response (201 Created)**:
```json
{
  "interaction_id": 123,
  "message": "Interaction started successfully"
}
```

**Response Schema**:
- `interaction_id` (integer): Newly created interaction ID
- `message` (string): Success message

**Error Responses**:
- `409 Conflict`: User already has an active interaction
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

**Performance Target**: < 200ms

**Notes**:
- Creates record in `conversation` table
- Initializes first 30-minute session timer
- Only one active interaction per user allowed
- Returns 409 if user already has active interaction

---

## 4. Transcript Append

### `POST /api/sessions/append`

**Called By**: Member A (Frontend/Detection)

**Purpose**: Append transcript chunk to active session

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "interaction_id": 123,
  "transcript_chunk": "So I was thinking about the appointment on Monday..."
}
```

**Request Schema**:
- `interaction_id` (integer, required): Interaction ID (positive integer)
- `transcript_chunk` (string, required): Transcript text (1-10,000 characters)

**Response (200 OK)**:
```json
{
  "message": "Transcript appended successfully"
}
```

**Response Schema**:
- `message` (string): Success message

**Error Responses**:
- `404 Not Found`: No active session for this interaction
- `413 Payload Too Large`: Transcript chunk exceeds 10,000 characters
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

**Performance Target**: < 100ms

**Notes**:
- Appends to `conversation.conversation` column in DB
- Transcript persisted immediately (no in-memory buffer)
- Max chunk size: 10,000 characters
- Call this endpoint as frequently as needed (real-time streaming)

---

## 5. Interaction End

### `POST /api/interactions/end`

**Called By**: Member A (Frontend/Detection)

**Purpose**: End interaction when person leaves, generate final summary

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "interaction_id": 123
}
```

**Request Schema**:
- `interaction_id` (integer, required): Interaction ID (positive integer)

**Response (200 OK)**:
```json
{
  "interaction_id": 123,
  "interaction_summary": "Discussed upcoming doctor appointment on Monday at 10 AM. User seemed concerned about transportation. Ravi offered to drive. Also talked about family gathering next weekend.",
  "message": "Interaction ended successfully"
}
```

**Response Schema**:
- `interaction_id` (integer): Interaction ID
- `interaction_summary` (string): Final merged summary (200 words or fewer)
- `message` (string): Success message

**Error Responses**:
- `404 Not Found`: Interaction not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

**Performance Target**: < 15 seconds (includes LLM calls)

**Notes**:
- Cancels active session timer
- Generates summary for current session
- Merges all session summaries into interaction summary
- Stores in `conversation.summarytext` column
- Clears in-memory session state
- This is an async operation (may take 5-15 seconds)

---

## 6. Memory Retrieval

### `GET /api/memory/{person_id}`

**Called By**: LangGraph agents, Member A (Frontend)

**Purpose**: Retrieve past interaction summaries for a person

**Request Headers**: None required

**Query Parameters**:
- `user_id` (integer, required): User ID (positive integer)

**Example Request**:
```
GET /api/memory/42?user_id=1
```

**Response (200 OK)**:
```json
{
  "person_id": 42,
  "summaries": [
    {
      "interaction_id": 120,
      "date": "2026-04-15T14:30:00Z",
      "summary": "Discussed hospital visit. Ravi seemed anxious. You promised to call him.",
      "location": "Living Room"
    },
    {
      "interaction_id": 115,
      "date": "2026-04-10T09:15:00Z",
      "summary": "Talked about work project deadlines. Ravi mentioned his daughter's graduation.",
      "location": "Kitchen"
    }
  ]
}
```

**Response Schema**:
- `person_id` (integer): Person ID
- `summaries` (array): Last 3 interaction summaries (ordered by date descending)
  - `interaction_id` (integer): Interaction ID
  - `date` (datetime): Interaction date
  - `summary` (string): Interaction summary text
  - `location` (string | null): Location

**Response - No Summaries (200 OK)**:
```json
{
  "person_id": 42,
  "summaries": []
}
```

**Error Responses**:
- `422 Unprocessable Entity`: Validation error (missing user_id)
- `500 Internal Server Error`: Server error

**Performance Target**: < 200ms

**Notes**:
- DB-only query (no LLM calls)
- Returns last 3 interactions with summaries
- Only returns completed interactions (summarytext is not null)
- Fast retrieval for real-time display

---

## 7. Note Creation

### `POST /api/notes`

**Called By**: Member B (Notes Agent)

**Purpose**: Store note and sync to Google Tasks

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "interaction_id": 123,
  "person_id": 42,
  "content": "Doctor appointment scheduled for Monday at 10 AM",
  "importance_level": 3
}
```

**Request Schema**:
- `interaction_id` (integer, required): Interaction ID (positive integer)
- `person_id` (integer, optional): Related person ID (positive integer)
- `content` (string, required): Note content (min 1 character)
- `importance_level` (integer, required): Importance level (1=low, 2=medium, 3=high)

**Response (201 Created)**:
```json
{
  "note_id": 456,
  "message": "Note created successfully",
  "sync_warning": null
}
```

**Response - With Sync Warning (201 Created)**:
```json
{
  "note_id": 456,
  "message": "Note created successfully",
  "sync_warning": "Failed to sync note to Google Tasks"
}
```

**Response Schema**:
- `note_id` (integer): Newly created note ID
- `message` (string): Success message
- `sync_warning` (string | null): Warning message if Google Tasks sync failed

**Error Responses**:
- `404 Not Found`: Interaction not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

**Performance Target**: < 500ms (including Google API call)

**Notes**:
- Stores in `note` table
- Syncs to Google Tasks if user has OAuth token
- Graceful degradation: note created even if sync fails
- Returns warning if sync fails (not an error)

---

## 8. Calendar Event Creation

### `POST /api/calendar/events`

**Called By**: Member B (Calendar Agent)

**Purpose**: Store calendar event and sync to Google Calendar

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "user_id": 1,
  "related_person_id": 42,
  "event_title": "Doctor Appointment",
  "event_datetime": "2026-04-21T10:00:00Z",
  "reminder_time": "2026-04-21T09:00:00Z"
}
```

**Request Schema**:
- `user_id` (integer, required): User ID (positive integer)
- `related_person_id` (integer, optional): Related person ID (positive integer)
- `event_title` (string, required): Event title (1-100 characters)
- `event_datetime` (datetime, required): Event date and time
- `reminder_time` (datetime, optional): Reminder date and time

**Response (201 Created)**:
```json
{
  "event_id": 789,
  "message": "Calendar event created successfully",
  "sync_warning": null
}
```

**Response - With Sync Warning (201 Created)**:
```json
{
  "event_id": 789,
  "message": "Calendar event created successfully",
  "sync_warning": "Failed to sync event to Google Calendar"
}
```

**Response Schema**:
- `event_id` (integer): Newly created event ID
- `message` (string): Success message
- `sync_warning` (string | null): Warning message if Google Calendar sync failed

**Error Responses**:
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

**Performance Target**: < 500ms (including Google API call)

**Notes**:
- Stores in `calendarevent` table
- Syncs to Google Calendar if user has OAuth token
- Graceful degradation: event created even if sync fails
- Returns warning if sync fails (not an error)
- Reminder calculated as minutes before event

---

## 9. Audio Transcription (Upload)

### `POST /api/audio/transcribe`

**Called By**: Member A (Frontend/Detection)

**Purpose**: Transcribe uploaded audio file and append to active session

**Request Headers**:
```
Content-Type: multipart/form-data
```

**Request Body** (Form Data):
- `audio` (file, required): Audio file (WAV, MP3, etc.)
- `interaction_id` (integer, required): Active interaction ID

**Response (200 OK)**:
```json
{
  "transcription": "Hello, how are you feeling today?",
  "interaction_id": 123,
  "message": "Audio transcribed successfully"
}
```

**Response Schema**:
- `transcription` (string): Transcribed text from audio
- `interaction_id` (integer): Interaction ID
- `message` (string): Success message

**Error Responses**:
- `404 Not Found`: No active session for this interaction
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Transcription failed

**Performance Target**: < 5 seconds (depends on audio length)

**Notes**:
- Uses OpenAI Whisper for transcription
- Automatically appends transcript to active session
- Supports WAV, MP3, M4A, and other common audio formats
- Audio file is deleted after processing

---

## 10. Audio Recording (Microphone)

### `POST /api/audio/record`

**Called By**: Testing/Development only

**Purpose**: Record audio from server's microphone and transcribe

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "user_id": 1,
  "person_id": 42,
  "duration_seconds": 10
}
```

**Request Schema**:
- `user_id` (integer, required): User ID (positive integer)
- `person_id` (integer, optional): Person ID (positive integer)
- `duration_seconds` (integer, optional): Recording duration (1-60 seconds, default: 10)

**Response (200 OK)**:
```json
{
  "transcription": "This is a test recording from the microphone.",
  "message": "Microphone recording processed successfully"
}
```

**Response Schema**:
- `transcription` (string): Transcribed text
- `message` (string): Success message

**Error Responses**:
- `408 Request Timeout`: No speech detected within timeout
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Recording failed

**Performance Target**: Recording duration + 3-5 seconds for transcription

**Notes**:
- **WARNING**: Uses server's microphone (not recommended for production)
- For production, use `/api/audio/transcribe` with client-side recording
- Requires microphone access on server machine
- Useful for testing and development only

---

## 11. Health Check

### `GET /health`

**Called By**: Monitoring tools, DevOps

**Purpose**: Verify system health and database connectivity

**Request Headers**: None required

**Response - Healthy (200 OK)**:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

**Response - Unhealthy (503 Service Unavailable)**:
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "error": "connection timeout"
}
```

**Response Schema**:
- `status` (string): "healthy" or "unhealthy"
- `database` (string): "connected" or "disconnected"
- `error` (string, optional): Error message if unhealthy

**Performance Target**: < 1 second

**Notes**:
- Simple database connectivity check
- Does not check external APIs (OpenAI, Google)
- Use for load balancer health checks

---

## Data Types Reference

### Integer IDs
All IDs in the system are **positive integers** (not UUIDs):
- `user_id`
- `person_id`
- `interaction_id`
- `note_id`
- `event_id`

### Face Encoding
- Type: Array of floats
- Dimensions: Exactly 128 or 512
- Format: JSON array
- Example: `[0.123, 0.456, 0.789, ...]`

### Datetime Format
- Format: ISO 8601 with timezone
- Example: `"2026-04-19T10:30:00Z"`
- Timezone: UTC (Z suffix)

### Importance Level
- Type: Integer
- Range: 1-3
- Values:
  - 1 = Low
  - 2 = Medium
  - 3 = High

### Priority Level
- Type: Integer
- Range: 1-5
- Values:
  - 1 = Lowest
  - 5 = Highest

---

## Error Response Format

All error responses follow this format:

```json
{
  "detail": "Error message here"
}
```

For validation errors (422):
```json
{
  "detail": [
    {
      "loc": ["body", "encoding"],
      "msg": "Face encoding must be exactly 128 or 512 dimensions",
      "type": "value_error"
    }
  ]
}
```

---

## Integration Workflow

### Member A (Frontend/Detection) Integration

**1. Person Detection Flow**:
```
1. Detect face → Extract encoding
2. POST /api/persons/identify
3. If person_id is null:
   - Prompt caregiver for name
   - POST /api/persons/register
4. Display person name + memory context
5. POST /api/interactions/start
6. Start streaming transcript
```

**2. Conversation Flow**:
```
1. Capture audio → Transcribe with Whisper
2. POST /api/sessions/append (every few seconds)
3. Repeat until person leaves
```

**3. Person Leaves Flow**:
```
1. Detect person left
2. POST /api/interactions/end
3. Wait for response (may take 5-15 seconds)
4. Display final summary
```

### Member B (Agents) Integration

**1. Notes Agent Flow**:
```
1. Receive conversation transcript
2. Extract important notes using LLM
3. For each note:
   - POST /api/notes
   - Check sync_warning in response
```

**2. Calendar Agent Flow**:
```
1. Receive conversation transcript
2. Extract calendar events using LLM
3. For each event:
   - POST /api/calendar/events
   - Check sync_warning in response
```

**3. LangGraph Orchestration**:
```
1. Supervisor receives transcript
2. Route to Notes Agent and Calendar Agent (parallel or sequential)
3. Collect results
4. Call backend endpoints with extracted data
```

---

## Configuration Requirements

### Member A Must Provide
- Face encoding dimensions (128 or 512)
- Transcript format (plain text)
- Person detection confidence threshold
- Person leave detection logic

### Member B Must Provide
- Agent output format (JSON schema)
- Execution mode (parallel or sequential)
- Error handling strategy

### Member C Must Confirm
- Database schema is finalized
- All tables exist
- Connection pooling settings

---

## Testing Checklist

### Before Integration Testing

- [ ] Member A: Confirm face encoding dimensions
- [ ] Member A: Test person identification endpoint
- [ ] Member A: Test interaction start/end flow
- [ ] Member B: Confirm agent output format
- [ ] Member B: Test note creation endpoint
- [ ] Member B: Test calendar event endpoint
- [ ] Member C: Confirm database schema
- [ ] All: Review this API contract document

### During Integration Testing

- [ ] Test full person detection → identification → interaction flow
- [ ] Test transcript streaming with real audio
- [ ] Test session timer expiration (30 minutes)
- [ ] Test interaction end with summary generation
- [ ] Test agent orchestration with real transcripts
- [ ] Test Google API sync (with and without tokens)
- [ ] Test error scenarios (network failures, timeouts)
- [ ] Test concurrent interactions (multiple users)

---

## Performance Benchmarks

| Endpoint | Target | Typical | Max Acceptable |
|----------|--------|---------|----------------|
| POST /api/persons/identify | < 500ms | 200-300ms | 1s |
| POST /api/persons/register | < 300ms | 100-200ms | 500ms |
| POST /api/interactions/start | < 200ms | 50-100ms | 500ms |
| POST /api/sessions/append | < 100ms | 20-50ms | 200ms |
| POST /api/interactions/end | < 15s | 5-10s | 30s |
| GET /api/memory/{person_id} | < 200ms | 50-100ms | 500ms |
| POST /api/notes | < 500ms | 200-300ms | 2s |
| POST /api/calendar/events | < 500ms | 200-300ms | 2s |
| POST /api/audio/transcribe | < 5s | 2-4s | 10s |
| POST /api/audio/record | varies | 10-15s | 65s |

---

## Support & Questions

For API contract questions or clarifications:
1. Check this document first
2. Review Swagger UI at http://localhost:8000/docs
3. Contact backend engineer
4. Schedule team sync if needed

**Last Updated**: 2026-04-19  
**Version**: 1.0.0  
**Status**: Ready for Integration Testing


---

## 10. User Management

### `POST /api/users/`

**Called By**: Frontend, Admin Panel

**Purpose**: Create a new user

**Request Body**:
```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "age": 65,
  "medicalcondition": "Short-term memory loss",
  "emergencycontact": "+1234567890"
}
```

**Response (201 Created)**:
```json
{
  "userid": 1,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "age": 65,
  "medicalcondition": "Short-term memory loss",
  "emergencycontact": "+1234567890",
  "createdat": "2026-04-19T10:30:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Email already exists
- `422 Unprocessable Entity`: Validation error

---

### `GET /api/users/{user_id}`

**Purpose**: Get user by ID

**Response (200 OK)**:
```json
{
  "userid": 1,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "age": 65,
  "medicalcondition": "Short-term memory loss",
  "emergencycontact": "+1234567890",
  "createdat": "2026-04-19T10:30:00Z"
}
```

**Error Responses**:
- `404 Not Found`: User not found

---

### `GET /api/users/`

**Purpose**: List all users with pagination

**Query Parameters**:
- `skip` (integer, default: 0): Number of records to skip
- `limit` (integer, default: 100, max: 1000): Maximum records to return

**Response (200 OK)**:
```json
{
  "users": [
    {
      "userid": 1,
      "name": "John Doe",
      "email": "john.doe@example.com",
      "age": 65,
      "medicalcondition": "Short-term memory loss",
      "emergencycontact": "+1234567890",
      "createdat": "2026-04-19T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

### `PUT /api/users/{user_id}`

**Purpose**: Update user information

**Request Body** (all fields optional):
```json
{
  "name": "John Smith",
  "age": 66,
  "medicalcondition": "Updated condition",
  "emergencycontact": "+0987654321",
  "email": "john.smith@example.com"
}
```

**Response (200 OK)**:
```json
{
  "userid": 1,
  "name": "John Smith",
  "email": "john.smith@example.com",
  "age": 66,
  "medicalcondition": "Updated condition",
  "emergencycontact": "+0987654321",
  "createdat": "2026-04-19T10:30:00Z"
}
```

**Error Responses**:
- `404 Not Found`: User not found
- `400 Bad Request`: Email already in use

---

### `DELETE /api/users/{user_id}`

**Purpose**: Delete a user

**Response (204 No Content)**: Empty response

**Error Responses**:
- `404 Not Found`: User not found

**WARNING**: This cascades and deletes all related data (interactions, notes, etc.)

---

### `GET /api/users/{user_id}/caregivers`

**Purpose**: Get all caregivers assigned to a user

**Response (200 OK)**:
```json
[
  {
    "caregiverid": 1,
    "name": "Jane Doe",
    "relationshiptouser": "daughter",
    "accesslevel": "admin"
  }
]
```

**Error Responses**:
- `404 Not Found`: User not found

---

### `GET /api/users/{user_id}/persons`

**Purpose**: Get all known persons for a user

**Response (200 OK)**:
```json
[
  {
    "personid": 1,
    "name": "Ravi Kumar",
    "relationshiptype": "colleague",
    "prioritylevel": 3,
    "notes": "Works in IT department"
  }
]
```

**Error Responses**:
- `404 Not Found`: User not found

---

## 11. Caregiver Management

### `POST /api/caregivers/`

**Called By**: Admin Panel, Frontend

**Purpose**: Create a new caregiver

**Request Body**:
```json
{
  "name": "Jane Doe",
  "relationshiptouser": "daughter",
  "accesslevel": "admin"
}
```

**Response (201 Created)**:
```json
{
  "caregiverid": 1,
  "name": "Jane Doe",
  "relationshiptouser": "daughter",
  "accesslevel": "admin"
}
```

---

### `GET /api/caregivers/{caregiver_id}`

**Purpose**: Get caregiver by ID

**Response (200 OK)**:
```json
{
  "caregiverid": 1,
  "name": "Jane Doe",
  "relationshiptouser": "daughter",
  "accesslevel": "admin"
}
```

**Error Responses**:
- `404 Not Found`: Caregiver not found

---

### `GET /api/caregivers/`

**Purpose**: List all caregivers with pagination

**Query Parameters**:
- `skip` (integer, default: 0): Number of records to skip
- `limit` (integer, default: 100, max: 1000): Maximum records to return

**Response (200 OK)**:
```json
{
  "caregivers": [
    {
      "caregiverid": 1,
      "name": "Jane Doe",
      "relationshiptouser": "daughter",
      "accesslevel": "admin"
    }
  ],
  "total": 1
}
```

---

### `PUT /api/caregivers/{caregiver_id}`

**Purpose**: Update caregiver information

**Request Body** (all fields optional):
```json
{
  "name": "Jane Smith",
  "relationshiptouser": "daughter",
  "accesslevel": "read"
}
```

**Response (200 OK)**:
```json
{
  "caregiverid": 1,
  "name": "Jane Smith",
  "relationshiptouser": "daughter",
  "accesslevel": "read"
}
```

**Error Responses**:
- `404 Not Found`: Caregiver not found

---

### `DELETE /api/caregivers/{caregiver_id}`

**Purpose**: Delete a caregiver

**Response (204 No Content)**: Empty response

**Error Responses**:
- `404 Not Found`: Caregiver not found

**Note**: This also removes all user-caregiver assignments

---

### `POST /api/caregivers/assign`

**Purpose**: Assign a caregiver to a user

**Request Body**:
```json
{
  "user_id": 1,
  "caregiver_id": 1
}
```

**Response (200 OK)**:
```json
{
  "message": "Caregiver 1 assigned to user 1"
}
```

**Error Responses**:
- `400 Bad Request`: User or caregiver not found, or already assigned
- `404 Not Found`: User or caregiver not found

---

### `POST /api/caregivers/unassign`

**Purpose**: Unassign a caregiver from a user

**Request Body**:
```json
{
  "user_id": 1,
  "caregiver_id": 1
}
```

**Response (200 OK)**:
```json
{
  "message": "Caregiver 1 unassigned from user 1"
}
```

**Error Responses**:
- `404 Not Found`: Assignment not found

---

## 12. Emotion Records

### `POST /api/emotions/`

**Called By**: Member A (Emotion Detection System)

**Purpose**: Create a new emotion record for an interaction

**Request Body**:
```json
{
  "interaction_id": 123,
  "emotiontype": "happy",
  "confidencelevel": 0.85
}
```

**Response (201 Created)**:
```json
{
  "emotionid": 1,
  "interactionid": 123,
  "emotiontype": "happy",
  "confidencelevel": 0.85
}
```

**Error Responses**:
- `404 Not Found`: Interaction not found
- `422 Unprocessable Entity`: Validation error

**Notes**:
- `emotiontype`: Common values include "happy", "sad", "angry", "neutral", "surprised", "fearful"
- `confidencelevel`: Float between 0.0 and 1.0

---

### `GET /api/emotions/{emotion_id}`

**Purpose**: Get emotion record by ID

**Response (200 OK)**:
```json
{
  "emotionid": 1,
  "interactionid": 123,
  "emotiontype": "happy",
  "confidencelevel": 0.85
}
```

**Error Responses**:
- `404 Not Found`: Emotion record not found

---

### `GET /api/emotions/interaction/{interaction_id}`

**Purpose**: Get all emotion records for a specific interaction

**Response (200 OK)**:
```json
[
  {
    "emotionid": 1,
    "interactionid": 123,
    "emotiontype": "happy",
    "confidencelevel": 0.85
  },
  {
    "emotionid": 2,
    "interactionid": 123,
    "emotiontype": "neutral",
    "confidencelevel": 0.72
  }
]
```

**Notes**:
- Useful for analyzing emotional patterns during a conversation
- Returns empty array if no emotions recorded

---

### `GET /api/emotions/`

**Purpose**: List all emotion records with pagination

**Query Parameters**:
- `skip` (integer, default: 0): Number of records to skip
- `limit` (integer, default: 100, max: 1000): Maximum records to return

**Response (200 OK)**:
```json
{
  "emotions": [
    {
      "emotionid": 1,
      "interactionid": 123,
      "emotiontype": "happy",
      "confidencelevel": 0.85
    }
  ],
  "total": 1
}
```

---

### `DELETE /api/emotions/{emotion_id}`

**Purpose**: Delete an emotion record

**Response (204 No Content)**: Empty response

**Error Responses**:
- `404 Not Found`: Emotion record not found

---

## Complete Endpoint Summary

### User Management
- `POST /api/users/` - Create user
- `GET /api/users/{user_id}` - Get user
- `GET /api/users/` - List users
- `PUT /api/users/{user_id}` - Update user
- `DELETE /api/users/{user_id}` - Delete user
- `GET /api/users/{user_id}/caregivers` - Get user's caregivers
- `GET /api/users/{user_id}/persons` - Get user's known persons

### Caregiver Management
- `POST /api/caregivers/` - Create caregiver
- `GET /api/caregivers/{caregiver_id}` - Get caregiver
- `GET /api/caregivers/` - List caregivers
- `PUT /api/caregivers/{caregiver_id}` - Update caregiver
- `DELETE /api/caregivers/{caregiver_id}` - Delete caregiver
- `POST /api/caregivers/assign` - Assign caregiver to user
- `POST /api/caregivers/unassign` - Unassign caregiver from user

### Person Management
- `POST /api/persons/identify` - Identify person by face encoding
- `POST /api/persons/register` - Register new person

### Interaction Management
- `POST /api/interactions/start` - Start interaction
- `POST /api/interactions/end` - End interaction with summary

### Session Management
- `POST /api/sessions/append` - Append transcript chunk

### Memory Retrieval
- `GET /api/memory/{person_id}` - Get past summaries

### Notes
- `POST /api/notes` - Create note + sync to Google Tasks

### Calendar
- `POST /api/calendar/events` - Create event + sync to Google Calendar

### Audio Transcription
- `POST /api/audio/transcribe` - Transcribe uploaded audio
- `POST /api/audio/record` - Record from server microphone (dev only)

### Emotion Records
- `POST /api/emotions/` - Create emotion record
- `GET /api/emotions/{emotion_id}` - Get emotion record
- `GET /api/emotions/interaction/{interaction_id}` - Get emotions for interaction
- `GET /api/emotions/` - List emotion records
- `DELETE /api/emotions/{emotion_id}` - Delete emotion record

### Health Check
- `GET /health` - Health check

---

## Database Schema Alignment

All endpoints now align with the actual PostgreSQL schema:

### Tables Covered
- ✅ `users` - User management endpoints
- ✅ `caregiver` - Caregiver management endpoints
- ✅ `knownperson` - Person identification/registration endpoints
- ✅ `conversation` - Interaction/session endpoints
- ✅ `faceencoding` - Used internally by person service
- ✅ `note` - Notes endpoints
- ✅ `calendarevent` - Calendar endpoints
- ✅ `emotionrecord` - Emotion record endpoints
- ✅ `usercaregiver` - Junction table (assign/unassign endpoints)
- ✅ `userknownperson` - Junction table (handled internally)

### Field Name Mapping
- Database uses lowercase without underscores: `userid`, `personid`, `caregiverid`
- API uses snake_case: `user_id`, `person_id`, `caregiver_id`
- ORM models use database naming
- Pydantic schemas use snake_case for API consistency

---

## Integration Checklist

### For Member A (Detection/Frontend)
- [ ] Use `POST /api/users/` to create users
- [ ] Use `POST /api/persons/identify` for face recognition
- [ ] Use `POST /api/persons/register` to register new persons
- [ ] Use `POST /api/interactions/start` when person detected
- [ ] Use `POST /api/audio/transcribe` for audio transcription
- [ ] Use `POST /api/emotions/` to record detected emotions
- [ ] Use `POST /api/interactions/end` when person leaves

### For Member B (Agents)
- [ ] Notes Agent: Use `POST /api/notes` to create notes
- [ ] Calendar Agent: Use `POST /api/calendar/events` to create events
- [ ] Both agents receive interaction summary from `POST /api/interactions/end`

### For Member C (Database)
- [ ] Verify all tables match schema.sql
- [ ] Ensure foreign key constraints are in place
- [ ] Test cascade deletes for user deletion
- [ ] Verify junction tables (usercaregiver, userknownperson)

### For Admin/Frontend
- [ ] Use user management endpoints for user CRUD
- [ ] Use caregiver management endpoints for caregiver CRUD
- [ ] Use assign/unassign endpoints for user-caregiver relationships
- [ ] Use emotion endpoints to view emotional patterns

---

## Performance Targets

| Endpoint | Target | Notes |
|----------|--------|-------|
| POST /api/persons/identify | < 500ms | Includes face matching + memory retrieval |
| POST /api/interactions/start | < 200ms | Simple DB insert |
| POST /api/interactions/end | < 5s | Includes LLM summarization |
| POST /api/sessions/append | < 100ms | Simple text append |
| GET /api/memory/{person_id} | < 200ms | DB-only, no LLM |
| POST /api/notes | < 3s | Includes Google Tasks sync |
| POST /api/calendar/events | < 3s | Includes Google Calendar sync |
| POST /api/audio/transcribe | < 10s | Depends on audio length |
| POST /api/users/ | < 200ms | Simple DB insert |
| POST /api/caregivers/ | < 200ms | Simple DB insert |
| POST /api/emotions/ | < 200ms | Simple DB insert |
| GET /health | < 100ms | Simple DB ping |

---

## Testing

### Swagger UI
Access interactive API documentation at: http://localhost:8000/docs

### ReDoc
Access alternative documentation at: http://localhost:8000/redoc

### Example Test Flow
```bash
# 1. Create a user
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com", "age": 65}'

# 2. Create a caregiver
curl -X POST http://localhost:8000/api/caregivers/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Doe", "relationshiptouser": "daughter", "accesslevel": "admin"}'

# 3. Assign caregiver to user
curl -X POST http://localhost:8000/api/caregivers/assign \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "caregiver_id": 1}'

# 4. Register a person
curl -X POST http://localhost:8000/api/persons/register \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "name": "Ravi Kumar", "relationship_type": "colleague", "encoding": [0.1, 0.2, ...]}'

# 5. Start interaction
curl -X POST http://localhost:8000/api/interactions/start \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "person_id": 1, "location": "Living Room"}'

# 6. Record emotion
curl -X POST http://localhost:8000/api/emotions/ \
  -H "Content-Type: application/json" \
  -d '{"interaction_id": 1, "emotiontype": "happy", "confidencelevel": 0.85}'

# 7. Transcribe audio
curl -X POST http://localhost:8000/api/audio/transcribe \
  -F "audio=@recording.wav" \
  -F "interaction_id=1"

# 8. End interaction
curl -X POST http://localhost:8000/api/interactions/end \
  -H "Content-Type: application/json" \
  -d '{"interaction_id": 1}'
```

---

**Last Updated**: April 19, 2026  
**Version**: 2.0.0  
**Status**: Complete - All schema tables covered
