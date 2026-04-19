# Cognitive Memory Assistant Backend

FastAPI-based backend server for the Cognitive Memory Assistant system. Provides memory retrieval, conversation management, and LLM-powered summarization for individuals with short-term memory loss.

## Architecture

### Two-Level Summary System
- **Sessions**: 30-minute conversation chunks managed by APScheduler
- **Interactions**: Complete visits containing one or more sessions
- Session summaries are merged into interaction summaries when person leaves
- Memory retrieval is DB-only (no LLM calls) for fast response

### Key Components
- **Person Service**: Face encoding matching with cosine similarity (threshold 0.6)
- **Interaction Manager**: Lifecycle management for person visits
- **Session Manager**: APScheduler-based 30-minute session boundaries
- **LLM Service**: OpenAI GPT-4o/3.5-turbo for summarization with retry logic
- **Memory Service**: Fast DB-only retrieval of past interaction summaries
- **Google Integration**: Calendar and Tasks API sync

## Tech Stack

- **API Server**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **LLM**: OpenAI API (GPT-4o or GPT-3.5-turbo)
- **Scheduler**: APScheduler (AsyncIOScheduler)
- **Google APIs**: Calendar API, Tasks API
- **Validation**: Pydantic v2
- **HTTP Client**: httpx (async)

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required configuration:
- Database connection (PostgreSQL)
- OpenAI API key
- Google OAuth credentials (optional, for Calendar/Tasks sync)

### 3. Database Setup

The database schema is managed by Member C. Ensure the PostgreSQL database is running and the schema is created.

### 4. Run the Server

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Person Management
- `POST /api/persons/identify` - Identify person by face encoding
- `POST /api/persons/register` - Register new person with face encoding

### Interaction Lifecycle
- `POST /api/interactions/start` - Start interaction when person detected
- `POST /api/interactions/end` - End interaction when person leaves

### Session Management
- `POST /api/sessions/append` - Append transcript chunk to active session

### Memory Retrieval
- `GET /api/memory/{person_id}` - Get last 3 interaction summaries (fast, DB-only)

### Notes & Calendar
- `POST /api/notes` - Create note and sync to Google Tasks
- `POST /api/calendar/events` - Create event and sync to Google Calendar

### Health Check
- `GET /health` - Health check endpoint for monitoring

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Key Features

### Face Identification
- Cosine similarity matching against stored face encodings
- Threshold: 0.6 (configurable)
- Returns person details + last 3 interaction summaries
- Response time: < 500ms

### Session Management
- Automatic 30-minute session boundaries
- APScheduler timers for session expiration
- Transcript accumulated in DB (conversation.conversation column)
- Session summaries stored in-memory buffer

### LLM Summarization
- Session summaries: 100 words or fewer
- Interaction summaries: 200 words or fewer
- Exponential backoff retry (3 attempts)
- Timeout: 30 seconds
- Fallback on failure

### Startup Recovery
- Clears orphaned session state on restart
- Cancels all APScheduler timers from previous run
- Logs warnings for incomplete sessions

### Google Integration
- OAuth2 authentication via user.google_token_json
- Syncs notes to Google Tasks
- Syncs events to Google Calendar
- Graceful degradation if sync fails

## Project Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI app, startup/shutdown
│   ├── config.py                  # Environment configuration
│   │
│   ├── api/routes/                # API endpoints
│   │   ├── persons.py
│   │   ├── interactions.py
│   │   ├── sessions.py
│   │   ├── memory.py
│   │   ├── notes.py
│   │   └── calendar_events.py
│   │
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── person.py
│   │   ├── conversation.py
│   │   ├── face_encoding.py
│   │   ├── note.py
│   │   └── calendar_event.py
│   │
│   ├── schemas/                   # Pydantic request/response models
│   │   ├── person.py
│   │   ├── interaction.py
│   │   ├── session.py
│   │   ├── memory.py
│   │   ├── note.py
│   │   └── calendar_event.py
│   │
│   ├── services/                  # Business logic
│   │   ├── person_service.py
│   │   ├── memory_service.py
│   │   ├── interaction_service.py
│   │   ├── session_service.py
│   │   ├── llm_service.py
│   │   ├── note_service.py
│   │   ├── calendar_service.py
│   │   ├── google_tasks.py
│   │   └── google_calendar.py
│   │
│   ├── core/                      # Core infrastructure
│   │   └── scheduler.py           # APScheduler singleton
│   │
│   └── db/                        # Database
│       ├── base.py                # SQLAlchemy engine
│       └── session.py             # Session factory
│
├── requirements.txt
├── .env.example
└── README.md
```

## Important Notes

### Database Schema
- Table names and column names match Member C's schema exactly
- IDs are integers (not UUIDs)
- Face encodings stored as TEXT (JSON serialized)
- Conversation table serves as interaction table

### Session State
- Active sessions tracked in-memory (lost on restart)
- Transcripts persisted to DB immediately
- Session summaries buffered in-memory until interaction ends

### One Active Interaction Per User
- System enforces only one active interaction per user at a time
- Returns 409 Conflict if attempting to start while one is active

### No LLM at Retrieval Time
- Memory retrieval is DB-only for speed (< 200ms)
- LLM only called during session close and interaction end

### Graceful Degradation
- Google API sync failures don't block note/event creation
- LLM failures use fallback summaries
- System continues operating if external services fail

## Team Integration

### Member A (Frontend/Detection)
- Sends face encodings to `POST /api/persons/identify`
- Calls `POST /api/interactions/start` when person detected
- Streams transcript chunks to `POST /api/sessions/append`
- Calls `POST /api/interactions/end` when person leaves

### Member B (Agents)
- Notes Agent and Calendar Agent extract information
- Call `POST /api/notes` and `POST /api/calendar/events`
- Backend handles Google API sync

### Member C (Database)
- Owns PostgreSQL schema and Alembic migrations
- Backend queries their tables via SQLAlchemy ORM

## Development

### Running Tests
```bash
pytest
```

### Code Style
```bash
black app/
ruff check app/
```

### Logging
- Structured JSON logging
- Levels: DEBUG, INFO, WARN, ERROR
- All API requests logged with INFO level
- External API failures logged with WARN level

## Production Considerations

1. **Database Connection Pooling**: Configured for 10-30 connections
2. **CORS**: Configure `CORS_ORIGINS` for production domains
3. **Secrets**: Never commit `.env` file
4. **Monitoring**: Use `/health` endpoint for health checks
5. **Scaling**: APScheduler uses in-memory job store (single instance only)
6. **Logging**: Configure log rotation and retention

## License

Proprietary - Cognitive Healthcare DBMS Project
