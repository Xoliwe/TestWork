from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.audit import AuditAction, Outcome
from app.db.session import get_db
from app.dependencies import Actor, require_roles
from app.models.facility import Facility, Practitioner
from app.models.role import STAFF_ROLES, Role
from app.schemas.auth import StaffCreate, UserOut
from app.services import audit_service, auth_service

router = APIRouter(prefix="/staff", tags=["staff"])


@router.post("", response_model=UserOut, status_code=201)
def create_staff(body: StaffCreate,
                 actor: Actor = Depends(require_roles(Role.SYSTEM_ADMIN, Role.FACILITY_ADMIN)),
                 db: Session = Depends(get_db)):
    if body.role not in STAFF_ROLES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Not a staff role")
    # Facility admins can only manage their own facility; they cannot mint other admins.
    if actor.user.role == Role.FACILITY_ADMIN:
        if body.facility_id != actor.staff.facility_id or body.role == Role.FACILITY_ADMIN:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Outside your administrative scope")
    if not db.get(Facility, body.facility_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Facility not found")

    user = auth_service.create_user(db, email=body.email, password=body.password,
                                    full_name=body.full_name, role=body.role)
    db.add(Practitioner(user_id=user.id, facility_id=body.facility_id,
                        professional_role=body.professional_role or body.role.value))
    audit_service.log(db, action=AuditAction.STAFF_CREATED, outcome=Outcome.SUCCESS,
                      user_id=actor.user.id, facility_id=body.facility_id,
                      resource=f"user/{user.id}", detail={"role": body.role.value})
    db.commit()
    return user
