# Migration Guide: Legacy Flask App → New FastAPI Backend

## Overview

The legacy Flask application (`app/`) has been merged into the new FastAPI backend (`backend/`). This document explains what was migrated, what changed, and how to use the new system.

## What Was Migrated

### ✅ Migrated Features

1. **Whisper Transcription Service**
   - **Legacy**: `app/ai_models/transcription/whisper_service.py`
   - **New**: `backend/app/services/whisper_service.py`
   - **Changes**: Added lazy loading and better logging

2. **Audio Upload Endpoint**
   - **Legacy**: `POST /api/audio/upload` (Flask)
   - **New**: `POST /api/audio/transcribe` (FastAPI)
   - **Changes**: 
     - Now integrates with session management
     - Automatically appends transcript to active session
     - Better error handling

3. **Microphone Recording Endpoint**
   - **Legacy**: `POST /api/audio/record_from_mic` (Flask)
   - **New**: `POST /api/audio/record` (FastAPI)
   - **Changes**:
     - Configurable recording duration
     - Better error messages
     - Marked as development-only

### ⚠️ Not Migrated (Deprecated)

1. **Reminder System** (`app/ai_models/reminders/`)
   - **Reason**: Replaced by Google Calendar integration
   - **Alternative**: Use `POST /api/calendar/events` with reminder_time

2. **Direct Database Inserts** (`app/database/db.py`)
   - **Reason**: Replaced by SQLAlchemy ORM and service layer
   - **Alternative**: Use interaction/session services

3. **Flask Routes** (`app/routes/`)
   - **Reason**: Replaced by FastAPI routers
   - **Alternative**: See API Contracts document

## API Changes

### Audio Transcription

**Legacy (Flask)**:
```bash
curl -X POST http://localhost:5000/api/audio/upload \
  -F "audio=@recording.wav" \
  -F "userid=1" \
  -F "personid=42"
```

**New (FastAPI)**:
```bash
curl -X POST http://localhost:8000/api/audio/transcribe \
  -F "audio=@recording.wav" \
  -F "interaction_id=123"
```

**Key Differences**:
- Uses `interaction_id` instead of `userid` and `personid`
- Must have an active interaction first (call `POST /api/interactions/start`)
- Automatically appends to active session
- Returns interaction_id in response

### Microphone Recording

**Legacy (Flask)**:
```bash
curl -X POST http://localhost:5000/api/audio/record_from_mic \
  -H "Content-Type: application/json" \
  -d '{"userid": 1, "personid": 42}'
```

**New (FastAPI)**:
```bash
curl -X POST http://localhost:8000/api/audio/record \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "person_id": 42, "duration_seconds": 10}'
```

**Key Differences**:
- Snake_case field names (`user_id` instead of `userid`)
- Configurable duration (1-60 seconds)
- Does NOT create interaction automatically
- For development/testing only

## Migration Workflow

### Old Workflow (Flask)
```
1. Upload audio → Transcribe → Insert to DB
2. Done
```

### New Workflow (FastAPI)
```
1. Detect person → POST /api/persons/identify
2. Start interaction → POST /api/interactions/start
3. Upload audio → POST /api/audio/transcribe (repeats)
4. Person leaves → POST /api/interactions/end
```

## Configuration Changes

### Environment Variables

**Legacy (.env)**:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password
```

**New (.env)** - Same, plus:
```env
# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o

# Session Management
SESSION_DURATION_MINUTES=30
FACE_SIMILARITY_THRESHOLD=0.60
LLM_TIMEOUT_SECONDS=30
```

### Dependencies

**Legacy (requirements.txt)**:
- Flask
- psycopg2
- whisper
- speech_recognition

**New (backend/requirements.txt)**:
- FastAPI
- SQLAlchemy
- openai-whisper
- SpeechRecognition
- Plus: APScheduler, LangGraph, Google APIs, etc.

## Running Both Systems (Transition Period)

If you need to run both systems during migration:

**Legacy Flask (Port 5000)**:
```bash
python app/app.py
```

**New FastAPI (Port 8000)**:
```bash
cd backend
python run.py
```

## Deprecation Timeline

| Component | Status | Deadline |
|-----------|--------|----------|
| Flask app | Deprecated | End of Week 5 |
| Legacy audio endpoints | Deprecated | End of Week 5 |
| Reminder system | Deprecated | Replaced by Google Calendar |
| Direct DB access | Deprecated | Use ORM services |

## Testing the Migration

### 1. Test Audio Transcription

```bash
# Start interaction first
curl -X POST http://localhost:8000/api/interactions/start \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "person_id": 1, "location": "Test"}'

# Note the interaction_id from response, then:
curl -X POST http://localhost:8000/api/audio/transcribe \
  -F "audio=@test.wav" \
  -F "interaction_id=1"
```

### 2. Test Microphone Recording

```bash
curl -X POST http://localhost:8000/api/audio/record \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "person_id": 1, "duration_seconds": 5}'
```

### 3. Verify Transcript Appended

```bash
# Check session has transcript
curl "http://localhost:8000/api/memory/1?user_id=1"
```

## Troubleshooting

### Issue: "No active session for this interaction"

**Cause**: Trying to transcribe audio without starting an interaction first

**Solution**: Call `POST /api/interactions/start` before transcribing

### Issue: "Microphone not found"

**Cause**: Server machine doesn't have a microphone

**Solution**: Use `POST /api/audio/transcribe` with client-side recording instead

### Issue: "Whisper model loading is slow"

**Cause**: First request loads the model (can take 10-30 seconds)

**Solution**: Model is cached after first load. Subsequent requests are fast.

### Issue: "Import error: No module named 'whisper'"

**Cause**: Missing dependencies

**Solution**: 
```bash
cd backend
pip install -r requirements.txt
```

## Benefits of New System

1. **Better Integration**: Audio transcription now integrates with session management
2. **Automatic Summarization**: Transcripts are automatically summarized by LLM
3. **Memory Context**: Past conversations are retrieved automatically
4. **Type Safety**: Pydantic validation prevents invalid data
5. **Better Docs**: Auto-generated Swagger UI at `/docs`
6. **Async Support**: Better performance for concurrent requests
7. **Structured Logging**: Better debugging and monitoring

## Support

For migration questions:
- Check API Contracts: `docs/API_CONTRACTS.md`
- Check Backend README: `docs/BACKEND_README.md`
- Check Swagger UI: http://localhost:8000/docs

---

**Migration Status**: ✅ Complete  
**Legacy System**: Deprecated (will be removed in Week 6)  
**New System**: Production-ready
