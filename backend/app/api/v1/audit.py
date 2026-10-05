from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import Actor, get_actor, require_roles
from app.models.audit_log import AuditLog
from app.models.role import Role

router = APIRouter(prefix="/audit", tags=["audit"])


def _row(a: AuditLog) -> dict:
    return {"id": str(a.id), "timestamp": a.timestamp, "user_id": a.user_id,
            "patient_id": a.patient_id, "facility_id": a.facility_id,
            "encounter_id": a.encounter_id, "action": a.action, "resource": a.resource,
            "outcome": a.outcome, "reason": a.reason}


@router.get("/my-access")
def my_access(limit: int = Query(100, le=500), actor: Actor = Depends(get_actor),
              db: Session = Depends(get_db)):
    """Staff: events they performed. Patients: who accessed THEIR record."""
    q = select(AuditLog)
    q = (q.where(AuditLog.patient_id == actor.user.patient_id) if actor.user.patient_id
         else q.where(AuditLog.user_id == actor.user.id))
    return [_row(a) for a in db.scalars(q.order_by(AuditLog.timestamp.desc()).limit(limit))]


@router.get("/facility")
def facility_audit(limit: int = Query(200, le=1000),
                   actor: Actor = Depends(require_roles(Role.FACILITY_ADMIN)),
                   db: Session = Depends(get_db)):
    q = (select(AuditLog).where(AuditLog.facility_id == actor.staff.facility_id)
         .order_by(AuditLog.timestamp.desc()).limit(limit))
    return [_row(a) for a in db.scalars(q)]
