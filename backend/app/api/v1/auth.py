from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import Actor, get_actor
from app.schemas.auth import LoginRequest, MeOut, TokenOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    return TokenOut(access_token=auth_service.authenticate(db, body.email, body.password))


@router.get("/me", response_model=MeOut)
def me(actor: Actor = Depends(get_actor)):
    u = actor.user
    return MeOut(id=u.id, email=u.email, full_name=u.full_name, role=u.role,
                 patient_id=u.patient_id,
                 facility_id=actor.staff.facility_id if actor.staff else None,
                 practitioner_id=actor.staff.id if actor.staff else None)
# Logout is client-side for stateless JWTs (short expiry). A token denylist can be added later.
