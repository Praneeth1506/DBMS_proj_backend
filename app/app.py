from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes.main_routes import main_router
from app.routes.audio_routes import audio_router
from app.routes.face_routes import face_router
from app.routes.interaction_routes import interaction_router
from app.ai_models.reminders.reminder_routes import reminder_router
from fastapi.staticfiles import StaticFiles

load_dotenv()

app = FastAPI(
    title="DBMS Project API",
    description="AI-powered memory assistant — audio transcription & face recognition.",
    version="1.0.0",
)

# Mount the static directory for the Frontend Dashboard
import os
os.makedirs("app/static", exist_ok=True)
app.mount("/dashboard", StaticFiles(directory="app/static", html=True), name="static")

# Allow all origins during development (tighten for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router)
app.include_router(audio_router)
app.include_router(face_router)
app.include_router(interaction_router)
app.include_router(reminder_router)