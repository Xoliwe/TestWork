import uuid

from sqlalchemy.orm import Session

from app.core.audit import AuditAction, Outcome
from app.models.audit_log import AuditLog


def log(db: Session, *, action: AuditAction, outcome: Outcome,
        user_id: uuid.UUID | None = None, patient_id: uuid.UUID | None = None,
        facility_id: uuid.UUID | None = None, encounter_id: uuid.UUID | None = None,
        resource: str | None = None, reason: str | None = None,
        detail: dict | None = None) -> AuditLog:
    """Adds an audit row to the current transaction. Caller commits (or use log_now)."""
    entry = AuditLog(action=action.value, outcome=outcome.value, user_id=user_id,
                     patient_id=patient_id, facility_id=facility_id, encounter_id=encounter_id,
                     resource=resource, reason=reason, detail=detail)
    db.add(entry)
    return entry


def log_now(db: Session, **kwargs) -> AuditLog:
    """Log and commit immediately, so the entry survives a rolled-back/failed request."""
    entry = log(db, **kwargs)
    db.commit()
    return entry
