import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedMixin, IdMixin


class Patient(IdMixin, CreatedMixin, Base):
    """Patient IDENTITY only. Medical data lives in separate tables."""
    __tablename__ = "patients"

    healthlink_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    # UNIQUE constraint = duplicate official identities are impossible at DB level.
    national_id: Mapped[str] = mapped_column(String(13), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    date_of_birth: Mapped[date] = mapped_column(Date)
    gender: Mapped[str] = mapped_column(String(20))
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    registered_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
