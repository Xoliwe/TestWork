import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.patient import PatientIdentityOut


class NoteCreate(BaseModel):
    record_type: Literal["consultation", "progress_note", "observation"] = "consultation"
    content: str = Field(min_length=1)


class DiagnosisCreate(BaseModel):
    code: str | None = None
    description: str = Field(min_length=1, max_length=500)


class MedicationCreate(BaseModel):
    medication_name: str
    dosage: str
    frequency: str


class AllergyCreate(BaseModel):
    substance: str
    reaction: str | None = None
    severity: Literal["mild", "moderate", "severe"] | None = None


class LabResultCreate(BaseModel):
    test_name: str
    result: str
    units: str | None = None
    reference_range: str | None = None


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    encounter_id: uuid.UUID
    facility_id: uuid.UUID
    created_at: datetime


class NoteOut(_Out):
    record_type: str
    content: str


class DiagnosisOut(_Out):
    code: str | None
    description: str


class MedicationOut(_Out):
    medication_name: str
    dosage: str
    frequency: str
    status: str


class AllergyOut(_Out):
    substance: str
    reaction: str | None
    severity: str | None


class LabResultOut(_Out):
    test_name: str
    result: str
    units: str | None
    reference_range: str | None


class MedicalRecordOut(BaseModel):
    patient: PatientIdentityOut
    allergies: list[AllergyOut]
    diagnoses: list[DiagnosisOut]
    medications: list[MedicationOut]
    lab_results: list[LabResultOut]
    notes: list[NoteOut]
    other_facilities_included: bool  # False = restricted to the requester's own facility
