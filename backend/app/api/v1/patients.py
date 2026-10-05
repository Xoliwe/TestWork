import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import AuditAction, Outcome
from app.core.permissions import Category
from app.db.session import get_db
from app.dependencies import Actor, require_roles
from app.models.patient import Patient
from app.models.role import Role
from app.schemas.patient import PatientCreate, PatientIdentityOut, PatientRegistrationOut
from app.services import audit_service, authorization_service as authz, patient_service

router = APIRouter(prefix="/patients", tags=["patients"])
_lookup_roles = (Role.RECEPTIONIST, Role.DOCTOR, Role.NURSE, Role.PATIENT)


@router.post("", response_model=PatientRegistrationOut, status_code=201)
def register_patient(body: PatientCreate, actor: Actor = Depends(require_roles(Role.RECEPTIONIST)),
                     db: Session = Depends(get_db)):
    """409 (via DuplicatePatientError handler) if the national ID already exists."""
    patient, token = patient_service.register_patient(db, body, actor.user, actor.staff)
    db.commit()
    return PatientRegistrationOut(patient=patient_service.to_identity(patient), qr_token=token)


@router.get("/by-healthlink-id/{healthlink_id}", response_model=PatientIdentityOut)
def by_healthlink_id(healthlink_id: str, actor: Actor = Depends(require_roles(*_lookup_roles)),
                     db: Session = Depends(get_db)):
    p = db.scalar(select(Patient).where(Patient.healthlink_id == healthlink_id.upper()))
    if p is None:
        audit_service.log_now(db, action=AuditAction.PATIENT_LOOKUP, outcome=Outcome.FAILURE,
                              user_id=actor.user.id, resource="healthlink_id")
        from fastapi import HTTPException
        raise HTTPException(404, "Patient not found")
    authz.require_patient_access(db, actor.user, actor.staff, p.id, Category.IDENTITY,
                                 AuditAction.PATIENT_LOOKUP)
    audit_service.log(db, action=AuditAction.PATIENT_LOOKUP, outcome=Outcome.ALLOWED,
                      user_id=actor.user.id, patient_id=p.id,
                      facility_id=actor.staff.facility_id if actor.staff else None)
    db.commit()
    return patient_service.to_identity(p)


@router.get("/{patient_id}", response_model=PatientIdentityOut)
def get_patient(patient_id: uuid.UUID, actor: Actor = Depends(require_roles(*_lookup_roles)),
                db: Session = Depends(get_db)):
    p = patient_service.get_or_404(db, patient_id)
    authz.require_patient_access(db, actor.user, actor.staff, p.id, Category.IDENTITY,
                                 AuditAction.PATIENT_LOOKUP)
    return patient_service.to_identity(p)


@router.post("/{patient_id}/qr/reissue", response_model=dict)
def reissue_qr(patient_id: uuid.UUID, actor: Actor = Depends(require_roles(Role.RECEPTIONIST)),
               db: Session = Depends(get_db)):
    """Lost/stolen card: revokes old QR, returns a new one (plaintext shown once)."""
    p = patient_service.get_or_404(db, patient_id)
    token = patient_service.issue_qr(db, p.id)
    audit_service.log(db, action=AuditAction.QR_ISSUED, outcome=Outcome.SUCCESS,
                      user_id=actor.user.id, patient_id=p.id,
                      facility_id=actor.staff.facility_id, reason="reissue")
    db.commit()
    return {"qr_token": token}
