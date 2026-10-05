import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedMixin, IdMixin, enum_col
from app.models.role import Role


class User(IdMixin, CreatedMixin, Base):
    """A login account. Patient accounts link to a Patient; staff link via Practitioner."""
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[Role] = mapped_column(enum_col(Role))
    status: Mapped[str] = mapped_column(String(20), default="active")
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("patients.id"), nullable=True, unique=True)
    failed_login_count: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


