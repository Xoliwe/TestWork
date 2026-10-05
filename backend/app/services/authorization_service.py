"""Central policy layer. Endpoints never decide access themselves."""
import enum
import uuid
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import AuditAction, Outcome
from app.core.permissions import ROLE_CATEGORIES, Category
from app.models.consent import CROSS_FACILITY_PURPOSE, Consent
from app.models.encounter import OPEN_STATUSES, Encounter
from app.models.facility import Practitioner
from app.models.role import Role
from app.models.user import User
from app.services import audit_service


class Decision(str, enum.Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    ALLOW_WITH_LIMITATIONS = "ALLOW_WITH_LIMITATIONS"


@dataclass
class AccessDecision:
    decision: Decision
    reason: str = ""
    encounter: Encounter | None = None
    include_other_facilities: bool = False

    @property
    def allowed(self) -> bool:
        return self.decision != Decision.DENY


def _deny(reason: str) -> AccessDecision:
    return AccessDecision(Decision.DENY, reason)


def has_cross_facility_consent(db: Session, patient_id: uuid.UUID) -> bool:
    return db.scalar(select(Consent.id).where(
        Consent.patient_id == patient_id, Consent.purpose == CROSS_FACILITY_PURPOSE,
        Consent.status == "granted").limit(1)) is not None


def can_access_patient(db: Session, user: User, staff: Practitioner | None,
                       patient_id: uuid.UUID, category: Category,
                       encounter_id: uuid.UUID | None = None) -> AccessDecision:
    # Patients: their own data only.
    if user.role == Role.PATIENT:
        if user.patient_id == patient_id:
            return AccessDecision(Decision.ALLOW, "self-access", include_other_facilities=True)
        return _deny("patients may only access their own record")

    if category not in ROLE_CATEGORIES.get(user.role, set()):
        return _deny(f"role '{user.role.value}' may not access {category.value} data")
    if staff is None or staff.status != "active":
        return _deny("no active facility membership")

    if category != Category.CLINICAL:
        return AccessDecision(Decision.ALLOW, "role permits non-clinical data")

    # Clinical data: needs an OPEN encounter for this patient at the clinician's facility.
    q = select(Encounter).where(Encounter.patient_id == patient_id,
                                Encounter.facility_id == staff.facility_id,
                                Encounter.status.in_(OPEN_STATUSES))
    if encounter_id:
        q = q.where(Encounter.id == encounter_id)
    enc = db.scalar(q)
    if enc is None:
        return _deny("no active encounter for this patient at your facility")
    # TODO (Phase 7): break-glass emergency grants plug in here.

    if has_cross_facility_consent(db, patient_id):
        return AccessDecision(Decision.ALLOW, "active encounter + cross-facility consent",
                              encounter=enc, include_other_facilities=True)
    return AccessDecision(Decision.ALLOW_WITH_LIMITATIONS,
                          "active encounter; records from other facilities withheld",
                          encounter=enc, include_other_facilities=False)


def require_patient_access(db: Session, user: User, staff: Practitioner | None,
                           patient_id: uuid.UUID, category: Category, action: AuditAction,
                           encounter_id: uuid.UUID | None = None) -> AccessDecision:
    d = can_access_patient(db, user, staff, patient_id, category, encounter_id)
    if not d.allowed:
        audit_service.log_now(db, action=action, outcome=Outcome.DENIED, user_id=user.id,
                              patient_id=patient_id,
                              facility_id=staff.facility_id if staff else None,
                              encounter_id=encounter_id, resource=category.value, reason=d.reason)
        raise HTTPException(status.HTTP_403_FORBIDDEN, d.reason)
    return d
