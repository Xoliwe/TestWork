from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.audit import AuditAction, Outcome
from app.db.session import get_db
from app.dependencies import Actor, require_roles
from app.models.role import Role
from app.schemas.auth import PatientAccountCreate, UserOut
from app.services import audit_service, auth_service, patient_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/patient-account", response_model=UserOut, status_code=201)
def create_patient_account(body: PatientAccountCreate,
                           actor: Actor = Depends(require_roles(Role.RECEPTIONIST)),
                           db: Session = Depends(get_db)):
    """Lets a registered patient log in to view their own record (MVP step 18)."""
    p = patient_service.get_or_404(db, body.patient_id)
    user = auth_service.create_user(db, email=body.email, password=body.password,
                                    full_name=f"{p.first_name} {p.last_name}",
                                    role=Role.PATIENT, patient_id=p.id)
    audit_service.log(db, action=AuditAction.USER_CREATED, outcome=Outcome.SUCCESS,
                      user_id=actor.user.id, patient_id=p.id, facility_id=actor.staff.facility_id)
    db.commit()
    return user
