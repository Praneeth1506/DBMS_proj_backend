from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from app.ai_models.reminders.tasks import remind_user
from pydantic import BaseModel
import redis

reminder_router = APIRouter(prefix="/api", tags=["Reminders"])

r = redis.Redis(host="localhost", port=6379, db=0)


class ReminderRequest(BaseModel):
    user_id: str
    message: str
    remind_at: str   # ISO 8601 — assumed to be in IST


@reminder_router.post("/schedule-reminder")
def schedule_reminder(body: ReminderRequest):
    """
    Schedule a reminder via Celery.

    - **user_id**: target user identifier
    - **message**: reminder text
    - **remind_at**: ISO datetime string in IST (e.g. `2026-04-19T10:30:00`)
    """
    remind_at = datetime.fromisoformat(body.remind_at)

    # Convert IST → UTC (IST = UTC + 5:30)
    remind_at_utc = remind_at - timedelta(hours=5, minutes=30)

    print(f"DEBUG: Local IST Target: {remind_at}")
    print(f"DEBUG: Internal UTC Target: {remind_at_utc}")

    remind_user.apply_async(args=[body.user_id, body.message], eta=remind_at_utc)
    return JSONResponse({"status": "Reminder scheduled", "at": str(remind_at)})


@reminder_router.get("/get-notifications/{user_id}")
def get_notifications(user_id: str):
    """
    Retrieve and drain pending notifications for a user from Redis.
    """
    msgs = []
    while True:
        item = r.rpop(f"notifications:{user_id}")
        if not item:
            break
        msgs.append(item.decode())
    return JSONResponse(msgs)