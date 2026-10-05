import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedMixin, IdMixin, utcnow


class _ClinicalBase(IdMixin, CreatedMixin):
    """Shared columns. facility_id enables cross-facility filtering."""
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    encounter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("encounters.id"), index=True)
    facility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id"))
    recorded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("practitioners.id"))


class ClinicalRecord(_ClinicalBase, Base):
    __tablename__ = "clinical_records"
    record_type: Mapped[str] = mapped_column(String(30))  # consultation | progress_note | observation
    content: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Diagnosis(_ClinicalBase, Base):
    __tablename__ = "diagnoses"
    code: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g. ICD-10
    description: Mapped[str] = mapped_column(String(500))


class Medication(_ClinicalBase, Base):
    __tablename__ = "medications"
    medication_name: Mapped[str] = mapped_column(String(200))
    dosage: Mapped[str] = mapped_column(String(100))
    frequency: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="active")


class Allergy(_ClinicalBase, Base):
    __tablename__ = "allergies"
    substance: Mapped[str] = mapped_column(String(200))
    reaction: Mapped[str | None] = mapped_column(String(300), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)


class LabResult(_ClinicalBase, Base):
    __tablename__ = "lab_results"
    test_name: Mapped[str] = mapped_column(String(200))
    result: Mapped[str] = mapped_column(String(200))
    units: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
