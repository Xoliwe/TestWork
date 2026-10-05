import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import AuditAction, Outcome
from app.core.permissions import Category
from app.models.clinical_record import (Allergy, ClinicalRecord, Diagnosis, LabResult,
                                        Medication)
from app.models.encounter import Encounter, EncounterStatus
from app.models.facility import Practitioner
from app.models.user import User
from app.schemas.clinical_record import MedicalRecordOut
from app.services import audit_service, authorization_service as authz, patient_service


def get_medical_record(db: Session, patient_id: uuid.UUID, user: User,
                       staff: Practitioner | None) -> MedicalRecordOut:
    d = authz.require_patient_access(db, user, staff, patient_id, Category.CLINICAL,
                                     AuditAction.VIEW_PATIENT_RECORD)
    patient = patient_service.get_or_404(db, patient_id)

    def fetch(model):
        q = select(model).where(model.patient_id == patient_id).order_by(model.created_at.desc())
        if not d.include_other_facilities:
            q = q.where(model.facility_id == staff.facility_id)
        return db.scalars(q).all()

    audit_service.log(db, action=AuditAction.VIEW_PATIENT_RECORD, outcome=Outcome.ALLOWED,
                      user_id=user.id, patient_id=patient_id,
                      facility_id=staff.facility_id if staff else None,
                      encounter_id=d.encounter.id if d.encounter else None,
                      resource="medical-record", reason=d.reason)
    return MedicalRecordOut(
        patient=patient_service.to_identity(patient), allergies=fetch(Allergy),
        diagnoses=fetch(Diagnosis), medications=fetch(Medication),
        lab_results=fetch(LabResult), notes=fetch(ClinicalRecord),
        other_facilities_included=d.include_other_facilities)


def add_record(db: Session, model, encounter_id: uuid.UUID, payload: dict,
               user: User, staff: Practitioner):
    """Writes require: clinician at the encounter's facility AND encounter IN_CONSULTATION."""
    enc = db.get(Encounter, encounter_id)
    if not enc or enc.facility_id != staff.facility_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Encounter not found")
    authz.require_patient_access(db, user, staff, enc.patient_id, Category.CLINICAL,
                                 AuditAction.CREATE_CLINICAL_RECORD, encounter_id=enc.id)
    if enc.status != EncounterStatus.IN_CONSULTATION:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Start the consultation before recording clinical data")
    row = model(patient_id=enc.patient_id, encounter_id=enc.id, facility_id=enc.facility_id,
                recorded_by=staff.id, **payload)
    db.add(row)
    db.flush()
    audit_service.log(db, action=AuditAction.CREATE_CLINICAL_RECORD, outcome=Outcome.SUCCESS,
                      user_id=user.id, patient_id=enc.patient_id, facility_id=enc.facility_id,
                      encounter_id=enc.id, resource=f"{model.__tablename__}/{row.id}")
    return row
