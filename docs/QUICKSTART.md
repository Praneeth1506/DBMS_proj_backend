# Quick Start Guide

## Prerequisites

- Python 3.10+
- PostgreSQL database (schema created by Member C)
- OpenAI API key
- (Optional) Google OAuth credentials for Calendar/Tasks sync

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set:
```env
# Required
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password

OPENAI_API_KEY=sk-your-key-here

# Optional (for Google sync)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-secret
```

### 3. Run the Server

```bash
# Option 1: Using the run script
python run.py

# Option 2: Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will start at: http://localhost:8000

## Testing the API

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 2. Register a Person

```bash
curl -X POST http://localhost:8000/api/persons/register \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "name": "John Doe",
    "relationship_type": "friend",
    "priority_level": 3,
    "encoding": [0.1, 0.2, 0.3, ... (128 or 512 floats)],
    "confidence_score": 0.95
  }'
```

### 3. Identify a Person

```bash
curl -X POST http://localhost:8000/api/persons/identify \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "encoding": [0.1, 0.2, 0.3, ... (128 or 512 floats)]
  }'
```

### 4. Start an Interaction

```bash
curl -X POST http://localhost:8000/api/interactions/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "person_id": 1,
    "location": "Living Room"
  }'
```

Response:
```json
{
  "interaction_id": 1,
  "message": "Interaction started successfully"
}
```

### 5. Append Transcript

```bash
curl -X POST http://localhost:8000/api/sessions/append \
  -H "Content-Type: application/json" \
  -d '{
    "interaction_id": 1,
    "transcript_chunk": "Hello, how are you today?"
  }'
```

### 6. End Interaction

```bash
curl -X POST http://localhost:8000/api/interactions/end \
  -H "Content-Type: application/json" \
  -d '{
    "interaction_id": 1
  }'
```

Response:
```json
{
  "interaction_id": 1,
  "interaction_summary": "Discussed daily activities and upcoming appointments...",
  "message": "Interaction ended successfully"
}
```

### 7. Retrieve Memory

```bash
curl "http://localhost:8000/api/memory/1?user_id=1"
```

Response:
```json
{
  "person_id": 1,
  "summaries": [
    {
      "interaction_id": 1,
      "date": "2026-04-19T10:30:00",
      "summary": "Discussed daily activities...",
      "location": "Living Room"
    }
  ]
}
```

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Common Issues

### Database Connection Error

**Error**: `could not connect to server`

**Solution**: Ensure PostgreSQL is running and credentials in `.env` are correct.

```bash
# Check PostgreSQL status
pg_isready -h localhost -p 5432
```

### OpenAI API Error

**Error**: `Invalid API key`

**Solution**: Verify your OpenAI API key in `.env`:

```bash
# Test your API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'app'`

**Solution**: Ensure you're running from the `backend` directory:

```bash
cd backend
python run.py
```

### Face Encoding Validation Error

**Error**: `Face encoding must be exactly 128 or 512 dimensions`

**Solution**: Ensure your face encoding array has exactly 128 or 512 float values.

## Development Tips

### Enable Debug Logging

Set in `.env`:
```env
APP_ENV=development
```

### Adjust Session Duration

Set in `.env`:
```env
SESSION_DURATION_MINUTES=5  # For testing (default: 30)
```

### Adjust Face Similarity Threshold

Set in `.env`:
```env
FACE_SIMILARITY_THRESHOLD=0.50  # Lower = more lenient (default: 0.60)
```

## Next Steps

1. **Integrate with Member A's Frontend**: Test face detection and transcript streaming
2. **Integrate with Member B's Agents**: Test note and calendar extraction
3. **Set up Google OAuth**: Enable Calendar and Tasks sync
4. **Load Testing**: Test with multiple concurrent interactions
5. **Production Deployment**: Configure for production environment

## Support

For issues or questions:
- Check `backend/README.md` for detailed documentation
- Check `backend/IMPLEMENTATION_SUMMARY.md` for architecture details
- Review API documentation at `/docs`
- Contact the backend engineer (you!)

---

**Happy coding! 🚀**
