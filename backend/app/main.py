"""
main.py — FastAPI application entry point
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.scheduler import start_scheduler, shutdown_scheduler, get_scheduler
from app.services.session_service import SessionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("Starting Cognitive Memory Assistant Backend...")
    settings = get_settings()
    
    # Start APScheduler
    start_scheduler()
    logger.info("APScheduler started")
    
    # Startup recovery: clear orphaned session state
    SessionManager.clear_all_sessions()
    scheduler = get_scheduler()
    scheduler.remove_all_jobs()
    logger.info("Cleared orphaned session state and timers")
    
    logger.info(f"Backend started in {settings.APP_ENV} mode")
    
    yield
    
    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("Shutting down Cognitive Memory Assistant Backend...")
    
    # Shutdown APScheduler
    shutdown_scheduler()
    logger.info("APScheduler shut down")
    
    logger.info("Backend shut down complete")


# Create FastAPI app
app = FastAPI(
    title="Cognitive Memory Assistant Backend",
    description="Backend API for memory retrieval, conversation management, and LLM-powered summarization",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
settings = get_settings()
origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring"""
    from app.db.base import get_engine
    from sqlalchemy import text
    
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


# ── Import and include routers ────────────────────────────────────────────────
from app.api.routes import (
    users,
    caregivers,
    persons,
    interactions,
    sessions,
    memory,
    notes,
    calendar_events,
    audio,
    emotions,
)

app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(caregivers.router, prefix="/api/caregivers", tags=["Caregivers"])
app.include_router(persons.router, prefix="/api/persons", tags=["Persons"])
app.include_router(interactions.router, prefix="/api/interactions", tags=["Interactions"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
app.include_router(notes.router, prefix="/api/notes", tags=["Notes"])
app.include_router(calendar_events.router, prefix="/api/calendar", tags=["Calendar"])
app.include_router(audio.router, prefix="/api/audio", tags=["Audio"])
app.include_router(emotions.router, prefix="/api/emotions", tags=["Emotions"])


# ── Root endpoint ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Cognitive Memory Assistant Backend API",
        "version": "1.0.0",
        "docs": "/docs",
    }
