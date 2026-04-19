"""
models/face_encoding.py — ORM model for public.faceencoding
Schema columns: faceencodingid, personid, encodingdata (TEXT), confidencescore, createdat

IMPORTANT: encodingdata is stored as TEXT in the actual DB schema (not JSONB).
We serialize/deserialize JSON in Python. Cosine similarity is done in application
code (sklearn), NOT in SQL.
"""
import json
from datetime import datetime
from sqlalchemy import Integer, Text, Numeric, TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class FaceEncoding(Base):
    __tablename__ = "faceencoding"
    __table_args__ = {"schema": "public"}

    faceencodingid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    personid: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("public.knownperson.personid")
    )
    encodingdata: Mapped[str | None] = mapped_column(Text)  # JSON-serialised float[]
    confidencescore: Mapped[float | None] = mapped_column(Numeric(5, 2))
    createdat: Mapped[datetime | None] = mapped_column(
        TIMESTAMP, default=datetime.utcnow
    )

    person = relationship("KnownPerson", back_populates="face_encodings")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def get_encoding_vector(self) -> list[float]:
        """Deserialise the TEXT column into a Python float list."""
        if self.encodingdata is None:
            return []
        return json.loads(self.encodingdata)

    @staticmethod
    def serialise_encoding(vector: list[float]) -> str:
        """Serialise a float list for storage in the TEXT column."""
        return json.dumps(vector)
