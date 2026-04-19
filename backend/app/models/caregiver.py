"""
models/caregiver.py — ORM model for public.caregiver
Schema columns: caregiverid, name, relationshiptouser, accesslevel
"""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Caregiver(Base):
    __tablename__ = "caregiver"
    __table_args__ = {"schema": "public"}

    caregiverid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(String(100))
    relationshiptouser: Mapped[str | None] = mapped_column(String(50))
    accesslevel: Mapped[str | None] = mapped_column(String(20))

    users = relationship(
        "User",
        secondary="public.usercaregiver",
        back_populates="caregivers",
    )
