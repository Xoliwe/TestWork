from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import Actor, require_roles
from app.models.role import Role
from app.schemas.encounter import CheckInRequest, EncounterOut
from app.schemas.patient import QRResolveOut, QRResolveRequest
from app.services import encounter_service, patient_service

router = APIRouter(tags=["check-in"])


@router.post("/qr/resolve", response_model=QRResolveOut)
def resolve_qr(body: QRResolveRequest,
               actor: Actor = Depends(require_roles(Role.RECEPTIONIST, Role.DOCTOR, Role.NURSE)),
               db: Session = Depends(get_db)):
    """Returns LIMITED identity only. Clinical data requires a separate authorised call."""
    out = patient_service.resolve_qr(db, body.qr_token, actor.user, actor.staff)
    db.commit()
    return out


@router.post("/encounters/check-in", response_model=EncounterOut, status_code=201)
def check_in(body: CheckInRequest, actor: Actor = Depends(require_roles(Role.RECEPTIONIST)),
             db: Session = Depends(get_db)):
    enc = encounter_service.check_in(db, body, actor.user, actor.staff)
    db.commit()
    return enc
