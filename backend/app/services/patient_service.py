import secrets
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import AuditAction, Outcome
from app.core.exceptions import DuplicatePatientError
from app.core.security import hash_token, new_qr_token
from app.db.base import as_utc, utcnow
from app.models.encounter import OPEN_STATUSES, Encounter
from app.models.facility import Practitioner
from app.models.patient import Patient
from app.models.qr_credential import QRCredential, QRStatus
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientIdentityOut, QRResolveOut
from app.services import audit_service

_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O/1/I


def _new_healthlink_id(db: Session) -> str:
    for _ in range(10):
        raw = "".join(secrets.choice(_ALPHABET) for _ in range(8))
        hid = f"HL-{raw[:4]}-{raw[4:]}"
        if not db.scalar(select(Patient.id).where(Patient.healthlink_id == hid)):
            return hid
    raise RuntimeError("Could not generate unique HealthLink ID")


def to_identity(p: Patient) -> PatientIdentityOut:
    return PatientIdentityOut(
        id=p.id, healthlink_id=p.healthlink_id, national_id_masked="*********" + p.national_id[-4:],
        first_name=p.first_name, last_name=p.last_name, date_of_birth=p.date_of_birth,
        gender=p.gender, phone=p.phone, email=p.email, address=p.address,
        emergency_contact_name=p.emergency_contact_name,
        emergency_contact_phone=p.emergency_contact_phone)


def get_or_404(db: Session, patient_id: uuid.UUID) -> Patient:
    p = db.get(Patient, patient_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")
    return p


def issue_qr(db: Session, patient_id: uuid.UUID) -> str:
    """Revokes any active QR for the patient and returns a fresh plaintext token (once)."""
    db.execute(update(QRCredential)
               .where(QRCredential.patient_id == patient_id, QRCredential.status == QRStatus.ACTIVE)
               .values(status=QRStatus.REVOKED, revoked_at=utcnow()))
    token = new_qr_token()
    db.add(QRCredential(patient_id=patient_id, token_hash=hash_token(token)))
    db.flush()
    return token


def register_patient(db: Session, data: PatientCreate, actor: User,
                     staff: Practitioner) -> tuple[Patient, str]:
    existing = db.scalar(select(Patient).where(Patient.national_id == data.national_id))
    if existing is None:
        patient = Patient(healthlink_id=_new_healthlink_id(db), registered_by=actor.id,
                          **data.model_dump())
        db.add(patient)
        try:
            db.flush()  # the UNIQUE constraint is the real guard against races
        except IntegrityError:
            db.rollback()
            existing = db.scalar(select(Patient).where(Patient.national_id == data.national_id))
    if existing is not None:
        audit_service.log_now(db, action=AuditAction.DUPLICATE_REGISTRATION_ATTEMPT,
                              outcome=Outcome.DENIED, user_id=actor.id, patient_id=existing.id,
                              facility_id=staff.facility_id, resource="patient")
        raise DuplicatePatientError(existing.healthlink_id)

    token = issue_qr(db, patient.id)
    audit_service.log(db, action=AuditAction.PATIENT_REGISTERED, outcome=Outcome.SUCCESS,
                      user_id=actor.id, patient_id=patient.id, facility_id=staff.facility_id,
                      resource="patient")
    audit_service.log(db, action=AuditAction.QR_ISSUED, outcome=Outcome.SUCCESS,
                      user_id=actor.id, patient_id=patient.id, facility_id=staff.facility_id)
    return patient, token


def resolve_qr(db: Session, token: str, actor: User, staff: Practitioner) -> QRResolveOut:
    cred = db.scalar(select(QRCredential).where(QRCredential.token_hash == hash_token(token)))
    valid = (cred is not None and cred.status == QRStatus.ACTIVE
             and (cred.expires_at is None or as_utc(cred.expires_at) > utcnow()))
    if not valid:
        audit_service.log_now(db, action=AuditAction.QR_SCAN, outcome=Outcome.DENIED,
                              user_id=actor.id, facility_id=staff.facility_id,
                              reason="invalid, revoked or expired QR")
        raise HTTPException(status.HTTP_404_NOT_FOUND, "QR code not recognised")

    patient = get_or_404(db, cred.patient_id)
    enc = db.scalar(select(Encounter).where(
        Encounter.patient_id == patient.id, Encounter.facility_id == staff.facility_id,
        Encounter.status.in_(OPEN_STATUSES)))
    audit_service.log(db, action=AuditAction.QR_SCAN, outcome=Outcome.SUCCESS, user_id=actor.id,
                      patient_id=patient.id, facility_id=staff.facility_id,
                      encounter_id=enc.id if enc else None)
    ident = to_identity(patient)
    return QRResolveOut(patient_id=patient.id, healthlink_id=patient.healthlink_id,
                        first_name=patient.first_name, last_name=patient.last_name,
                        date_of_birth=patient.date_of_birth,
                        national_id_masked=ident.national_id_masked,
                        active_encounter_id=enc.id if enc else None,
                        active_encounter_status=enc.status.value if enc else None)
