import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import Actor, require_roles
from app.models.role import Role
from app.schemas.encounter import EncounterOut, WaitingEntry
from app.services import encounter_service

router = APIRouter(prefix="/encounters", tags=["encounters"])
_staff = (Role.RECEPTIONIST, Role.DOCTOR, Role.NURSE)


@router.get("/waiting", response_model=list[WaitingEntry])
def waiting(actor: Actor = Depends(require_roles(*_staff)), db: Session = Depends(get_db)):
    return encounter_service.waiting_queue(db, actor.staff)


@router.get("/{encounter_id}", response_model=EncounterOut)
def get_encounter(encounter_id: uuid.UUID, actor: Actor = Depends(require_roles(*_staff)),
                  db: Session = Depends(get_db)):
    return encounter_service.get_encounter(db, encounter_id, actor.staff)


@router.post("/{encounter_id}/start", response_model=EncounterOut)
def start(encounter_id: uuid.UUID, actor: Actor = Depends(require_roles(Role.DOCTOR, Role.NURSE)),
          db: Session = Depends(get_db)):
    enc = encounter_service.start_consultation(db, encounter_id, actor.user, actor.staff)
    db.commit()
    return enc


@router.post("/{encounter_id}/checkout", response_model=EncounterOut)
def checkout(encounter_id: uuid.UUID, actor: Actor = Depends(require_roles(*_staff)),
             db: Session = Depends(get_db)):
    enc = encounter_service.checkout(db, encounter_id, actor.user, actor.staff)
    db.commit()
    return enc
