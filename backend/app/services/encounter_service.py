import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import AuditAction, Outcome
from app.db.base import utcnow
from app.models.encounter import OPEN_STATUSES, Encounter, EncounterStatus
from app.models.facility import Practitioner
from app.models.role import CLINICIAN_ROLES
from app.models.user import User
from app.schemas.encounter import CheckInRequest, WaitingEntry
from app.services import audit_service, patient_service


def _get_at_facility(db: Session, encounter_id: uuid.UUID, staff: Practitioner) -> Encounter:
    enc = db.get(Encounter, encounter_id)
    # 404 (not 403) for other facilities' encounters so existence isn't leaked.
    if not enc or enc.facility_id != staff.facility_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Encounter not found")
    return enc


def get_encounter(db, encounter_id, staff):
    return _get_at_facility(db, encounter_id, staff)


def check_in(db: Session, data: CheckInRequest, user: User, staff: Practitioner) -> Encounter:
    patient = patient_service.get_or_404(db, data.patient_id)
    open_enc = db.scalar(select(Encounter.id).where(
        Encounter.patient_id == patient.id, Encounter.facility_id == staff.facility_id,
        Encounter.status.in_(OPEN_STATUSES)))
    if open_enc:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Patient already has an open encounter at this facility")

    if data.practitioner_id:  # appointment with a specific clinician
        prac = db.get(Practitioner, data.practitioner_id)
        if not prac or prac.facility_id != staff.facility_id or prac.status != "active":
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                                "Practitioner not found at this facility")

    enc = Encounter(patient_id=patient.id, facility_id=staff.facility_id, reason=data.reason,
                    payment_reference=data.payment_reference, appointment_id=data.appointment_id,
                    practitioner_id=data.practitioner_id, checked_in_by=user.id,
                    status=EncounterStatus.CHECKED_IN)
    db.add(enc)
    db.flush()
    audit_service.log(db, action=AuditAction.PATIENT_CHECK_IN, outcome=Outcome.SUCCESS,
                      user_id=user.id, patient_id=patient.id, facility_id=staff.facility_id,
                      encounter_id=enc.id)
    return enc


def waiting_queue(db: Session, staff: Practitioner) -> list[WaitingEntry]:
    rows = db.scalars(select(Encounter).where(
        Encounter.facility_id == staff.facility_id,
        Encounter.status == EncounterStatus.CHECKED_IN).order_by(Encounter.checked_in_at)).all()
    return [WaitingEntry(encounter_id=e.id, patient_id=e.patient_id,
                         healthlink_id=e.patient.healthlink_id,
                         patient_name=f"{e.patient.first_name} {e.patient.last_name}",
                         reason=e.reason, checked_in_at=e.checked_in_at,
                         assigned_practitioner_id=e.practitioner_id, status=e.status.value)
            for e in rows]


def start_consultation(db: Session, encounter_id: uuid.UUID, user: User,
                       staff: Practitioner) -> Encounter:
    if user.role not in CLINICIAN_ROLES:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only clinicians can start a consultation")
    enc = _get_at_facility(db, encounter_id, staff)
    if enc.status != EncounterStatus.CHECKED_IN:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Encounter is {enc.status.value}")
    if enc.practitioner_id and enc.practitioner_id != staff.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Encounter is booked with another practitioner")
    enc.practitioner_id = staff.id  # walk-ins get their clinician here
    enc.status = EncounterStatus.IN_CONSULTATION
    enc.started_at = utcnow()
    audit_service.log(db, action=AuditAction.CONSULTATION_STARTED, outcome=Outcome.SUCCESS,
                      user_id=user.id, patient_id=enc.patient_id, facility_id=enc.facility_id,
                      encounter_id=enc.id)
    return enc


def checkout(db: Session, encounter_id: uuid.UUID, user: User, staff: Practitioner) -> Encounter:
    enc = _get_at_facility(db, encounter_id, staff)
    if enc.status not in OPEN_STATUSES:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Encounter is {enc.status.value}")
    enc.status = EncounterStatus.COMPLETED
    enc.ended_at = utcnow()
    audit_service.log(db, action=AuditAction.PATIENT_CHECK_OUT, outcome=Outcome.SUCCESS,
                      user_id=user.id, patient_id=enc.patient_id, facility_id=enc.facility_id,
                      encounter_id=enc.id)
    return enc
