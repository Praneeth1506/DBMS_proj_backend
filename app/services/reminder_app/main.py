from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.services.reminder_app.google_auth import get_auth_url, exchange_code_for_token
from app.services.reminder_app.calendar_service import create_reminder, get_upcoming_reminders
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

import os
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

class ReminderRequest(BaseModel):
    title: str
    date: str   # "2026-04-20"
    time: str   # "10:30"

@app.get("/")
def home(request: Request):
    try:
        return templates.TemplateResponse(request=request, name="index.html")
    except Exception as e:
        import traceback
        return JSONResponse(status_code=500, content={"error": str(e), "trace": traceback.format_exc()})

@app.get("/auth")
def auth():
    url = get_auth_url()
    return RedirectResponse(url)

@app.get("/oauth2callback")
def oauth_callback(code: str):
    exchange_code_for_token(code)
    return RedirectResponse("/")

@app.post("/create-reminder")
def add_reminder(data: ReminderRequest):
    event = create_reminder(data.title, data.date, data.time)
    return {"status": "created", "event_id": event.get("id")}

@app.get("/get-reminders")
def reminders():
    events = get_upcoming_reminders()
    return JSONResponse(events)