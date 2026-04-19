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

## 9. Health Check

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
