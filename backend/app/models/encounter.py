import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, enum_col, utcnow


class EncounterStatus(str, enum.Enum):
    CHECKED_IN = "checked_in"
    IN_CONSULTATION = "in_consultation"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


OPEN_STATUSES = (EncounterStatus.CHECKED_IN, EncounterStatus.IN_CONSULTATION)


class Encounter(IdMixin, Base):
    """A visit. practitioner_id is NULL until a clinician takes the patient (walk-ins)."""
    __tablename__ = "encounters"
    __table_args__ = (Index("ix_enc_facility_status", "facility_id", "status"),
                      Index("ix_enc_patient_status", "patient_id", "status"))

    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"))
    facility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id"))
    practitioner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("practitioners.id"), nullable=True)
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)  # appointments module later
    reason: Mapped[str] = mapped_column(String(500))
    payment_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[EncounterStatus] = mapped_column(
        enum_col(EncounterStatus), default=EncounterStatus.CHECKED_IN)
    checked_in_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    checked_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    patient = relationship("Patient", lazy="joined")
