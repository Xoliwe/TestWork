import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CheckInRequest(BaseModel):
    patient_id: uuid.UUID
    reason: str = Field(min_length=2, max_length=500)
    payment_reference: str | None = None
    appointment_id: uuid.UUID | None = None
    practitioner_id: uuid.UUID | None = None  # only for appointments with a specific doctor


class EncounterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    patient_id: uuid.UUID
    facility_id: uuid.UUID
    practitioner_id: uuid.UUID | None
    appointment_id: uuid.UUID | None
    reason: str
    status: str
    checked_in_at: datetime
    started_at: datetime | None
    ended_at: datetime | None


class WaitingEntry(BaseModel):
    encounter_id: uuid.UUID
    patient_id: uuid.UUID
    healthlink_id: str
    patient_name: str
    reason: str
    checked_in_at: datetime
    assigned_practitioner_id: uuid.UUID | None
    status: str
