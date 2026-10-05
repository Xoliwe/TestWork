from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import AuditAction, Outcome
from app.db.session import get_db
from app.dependencies import Actor, get_actor, require_roles
from app.models.facility import Facility
from app.models.role import Role
from app.schemas.auth import FacilityCreate, FacilityOut
from app.services import audit_service

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.post("", response_model=FacilityOut, status_code=201)
def create_facility(body: FacilityCreate, actor: Actor = Depends(require_roles(Role.SYSTEM_ADMIN)),
                    db: Session = Depends(get_db)):
    f = Facility(**body.model_dump())
    db.add(f)
    db.flush()
    audit_service.log(db, action=AuditAction.FACILITY_CREATED, outcome=Outcome.SUCCESS,
                      user_id=actor.user.id, facility_id=f.id)
    db.commit()
    return f


@router.get("", response_model=list[FacilityOut])
def list_facilities(_: Actor = Depends(get_actor), db: Session = Depends(get_db)):
    return db.scalars(select(Facility).where(Facility.status == "active")).all()
