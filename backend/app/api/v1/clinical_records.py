import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import Actor, require_roles
from app.models.clinical_record import (Allergy, ClinicalRecord, Diagnosis, LabResult,
                                        Medication)
from app.models.role import Role
from app.schemas import clinical_record as s
from app.services import clinical_service

router = APIRouter(tags=["clinical-records"])
_clin = (Role.DOCTOR, Role.NURSE)


@router.get("/patients/{patient_id}/medical-record", response_model=s.MedicalRecordOut)
def medical_record(patient_id: uuid.UUID,
                   actor: Actor = Depends(require_roles(Role.DOCTOR, Role.NURSE, Role.PATIENT)),
                   db: Session = Depends(get_db)):
    out = clinical_service.get_medical_record(db, patient_id, actor.user, actor.staff)
    db.commit()  # persists the access audit entry
    return out


def _add(model, body, encounter_id, actor, db):
    row = clinical_service.add_record(db, model, encounter_id, body.model_dump(),
                                      actor.user, actor.staff)
    db.commit()
    return row


@router.post("/encounters/{encounter_id}/notes", response_model=s.NoteOut, status_code=201)
def add_note(encounter_id: uuid.UUID, body: s.NoteCreate,
             actor: Actor = Depends(require_roles(*_clin)), db: Session = Depends(get_db)):
    return _add(ClinicalRecord, body, encounter_id, actor, db)


@router.post("/encounters/{encounter_id}/allergies", response_model=s.AllergyOut, status_code=201)
def add_allergy(encounter_id: uuid.UUID, body: s.AllergyCreate,
                actor: Actor = Depends(require_roles(*_clin)), db: Session = Depends(get_db)):
    return _add(Allergy, body, encounter_id, actor, db)


@router.post("/encounters/{encounter_id}/lab-results", response_model=s.LabResultOut,
             status_code=201)
def add_lab(encounter_id: uuid.UUID, body: s.LabResultCreate,
            actor: Actor = Depends(require_roles(*_clin)), db: Session = Depends(get_db)):
    return _add(LabResult, body, encounter_id, actor, db)


# Prescribing and diagnosing are doctor-only.
@router.post("/encounters/{encounter_id}/diagnoses", response_model=s.DiagnosisOut,
             status_code=201)
def add_diagnosis(encounter_id: uuid.UUID, body: s.DiagnosisCreate,
                  actor: Actor = Depends(require_roles(Role.DOCTOR)), db: Session = Depends(get_db)):
    return _add(Diagnosis, body, encounter_id, actor, db)


@router.post("/encounters/{encounter_id}/medications", response_model=s.MedicationOut,
             status_code=201)
def add_medication(encounter_id: uuid.UUID, body: s.MedicationCreate,
                   actor: Actor = Depends(require_roles(Role.DOCTOR)),
                   db: Session = Depends(get_db)):
    return _add(Medication, body, encounter_id, actor, db)
