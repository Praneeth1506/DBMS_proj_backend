# Cognitive Memory Assistant - DBMS Project

Backend system for an Agentic AI-based Cognitive Memory Assistant for individuals with short-term memory loss.

## Project Structure

```
.
├── backend/               # FastAPI backend (NEW - Week 1-4 implementation)
│   ├── app/              # Application code
│   ├── tests/            # Unit tests
│   └── requirements.txt  # Backend dependencies
├── app/                  # Legacy application code
├── database/             # Database schema (Member C)
├── docs/                 # Documentation
└── requirements.txt      # Root dependencies
```

## Quick Start

### Backend Server (FastAPI)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python run.py
```

Server starts at: http://localhost:8000  
API docs: http://localhost:8000/docs

### Legacy App

```bash
pip install -r requirements.txt
python app/app.py
```

## Documentation

- [Backend README](./docs/BACKEND_README.md) - Comprehensive backend guide
- [Quick Start Guide](./docs/QUICKSTART.md) - Get started quickly
- [Implementation Summary](./docs/IMPLEMENTATION_SUMMARY.md) - Architecture and status
- [API Contracts](./docs/API_CONTRACTS.md) - Team integration guide

## Team Responsibilities

- **Backend Engineer (You)**: FastAPI, services, LLM, Google APIs, APScheduler, LangGraph
- **Member A**: YOLO detection, DeepFace, Whisper STT, Emotion detection
- **Member B**: Notes Agent, Calendar Agent logic
- **Member C**: PostgreSQL schema, Alembic migrations
- **Member D**: Floater support

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **LLM**: OpenAI GPT-4o/3.5-turbo
- **Scheduler**: APScheduler
- **Google APIs**: Calendar, Tasks
- **Agent Framework**: LangGraph

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password_here

# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth2callback
CALENDAR_ID=primary

# App Configuration
APP_ENV=development
SESSION_DURATION_MINUTES=30
FACE_SIMILARITY_THRESHOLD=0.60
LLM_TIMEOUT_SECONDS=30
MEMORY_CONTEXT_LIMIT=3
```

## Development

### Install Dependencies
```bash
pip install -r requirements.txt
cd backend && pip install -r requirements.txt
```

### Run Tests
```bash
cd backend
pytest
```

### Code Style
```bash
black backend/app/
ruff check backend/app/
```

## License

Proprietary - Cognitive Healthcare DBMS Project
