import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, utcnow


class AuditLog(IdMixin, Base):
    """Append-only by convention: the app never updates or deletes rows."""
    __tablename__ = "audit_logs"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(index=True, nullable=True)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(index=True, nullable=True)
    facility_id: Mapped[uuid.UUID | None] = mapped_column(index=True, nullable=True)
    encounter_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    action: Mapped[str] = mapped_column(String(50), index=True)
    resource: Mapped[str | None] = mapped_column(String(100), nullable=True)
    outcome: Mapped[str] = mapped_column(String(20))  # allowed | denied | success | failure
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
