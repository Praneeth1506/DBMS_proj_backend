# Cognitive Memory Assistant

An AI-powered backend system for a Cognitive Memory Assistant designed to help individuals with short-term memory loss. The system uses face recognition, audio transcription, and LLM-powered summarization to provide contextual memory assistance.

## Overview

This FastAPI backend provides a complete REST API for managing users, caregivers, known persons, interactions, and memory retrieval. It integrates with OpenAI for LLM summarization, Whisper for speech-to-text, and Google APIs for calendar and task management.

## Features

- **User & Caregiver Management**: Complete CRUD operations
- **Face Recognition**: Identify persons using face encoding with cosine similarity
- **Interaction Tracking**: Start/end interactions with automatic session management
- **Audio Transcription**: Whisper STT integration for audio-to-text
- **LLM Summarization**: Automatic conversation summarization using OpenAI GPT-4
- **Memory Retrieval**: Fast database lookups for past interactions
- **Emotion Tracking**: Record and analyze emotions during interactions
- **Google Integration**: Sync notes to Google Tasks and events to Google Calendar
- **Auto-generated API Docs**: Interactive Swagger UI and ReDoc

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL database
- OpenAI API key (for LLM features)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Vishal17082k06/DBMS_proj_backend.git
cd DBMS_proj_backend
```

2. **Install dependencies**
```bash
cd backend
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database credentials and API keys
```

4. **Run the server**
```bash
python run.py
```

The server will start at: **http://localhost:8000**

### Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password

# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-secret

# App Configuration
SESSION_DURATION_MINUTES=30
FACE_SIMILARITY_THRESHOLD=0.60
LLM_TIMEOUT_SECONDS=30
```

## Project Structure

```
backend/
├── app/
│   ├── api/routes/      # API endpoints
│   ├── services/        # Business logic
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic request/response schemas
│   ├── db/              # Database configuration
│   └── core/            # Core utilities (scheduler, etc.)
├── tests/               # Unit tests
├── requirements.txt     # Python dependencies
└── run.py              # Application entry point
```

## API Endpoints

### Core Endpoints
- User Management: 7 endpoints
- Caregiver Management: 7 endpoints
- Person Management: 2 endpoints
- Interaction Management: 2 endpoints
- Emotion Records: 5 endpoints
- Notes & Calendar: 2 endpoints
- Audio Transcription: 2 endpoints

**Total**: 27 REST API endpoints

See [API Contracts](./docs/API_CONTRACTS.md) for complete API documentation.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **LLM**: OpenAI GPT-4o/3.5-turbo
- **Speech-to-Text**: OpenAI Whisper
- **Scheduler**: APScheduler
- **External APIs**: Google Calendar, Google Tasks
- **Validation**: Pydantic v2

## Development

### Run Tests
```bash
cd backend
pytest
```

### Code Formatting
```bash
black backend/app/
ruff check backend/app/
```

## Documentation

- [API Contracts](./docs/API_CONTRACTS.md) - Complete API reference
- [Backend README](./docs/BACKEND_README.md) - Detailed backend documentation
- [Quick Start Guide](./docs/QUICKSTART.md) - Getting started guide
- [New Endpoints Guide](./docs/NEW_ENDPOINTS_GUIDE.md) - Quick reference for new endpoints

## License

Proprietary - Cognitive Healthcare DBMS Project
