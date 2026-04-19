# models/__init__.py — imports all models so SQLAlchemy registers metadata
from app.models.junction_tables import usercaregiver, userknownperson  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.caregiver import Caregiver  # noqa: F401
from app.models.person import KnownPerson  # noqa: F401
from app.models.face_encoding import FaceEncoding  # noqa: F401
from app.models.conversation import Conversation  # noqa: F401
from app.models.note import Note  # noqa: F401
from app.models.calendar_event import CalendarEvent  # noqa: F401
