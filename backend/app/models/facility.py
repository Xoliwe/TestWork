import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedMixin, IdMixin


class Facility(IdMixin, CreatedMixin, Base):
    __tablename__ = "facilities"

    name: Mapped[str] = mapped_column(String(200), unique=True)
    facility_type: Mapped[str] = mapped_column(String(50))  # hospital | clinic | laboratory
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")


class Practitioner(IdMixin, CreatedMixin, Base):
    """Facility membership for any staff user (reception, doctor, nurse, facility admin)."""
    __tablename__ = "practitioners"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    facility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id"), index=True)
    professional_role: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="active")
