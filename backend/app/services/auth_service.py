from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.audit import AuditAction, Outcome
from app.core.security import DUMMY_HASH, create_access_token, hash_password, verify_password
from app.db.base import as_utc, utcnow
from app.models.user import User
from app.services import audit_service

_BAD = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")


def authenticate(db: Session, email: str, password: str) -> str:
    email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        verify_password(password, DUMMY_HASH)
        audit_service.log_now(db, action=AuditAction.LOGIN_FAILED, outcome=Outcome.FAILURE,
                              reason="unknown email")
        raise _BAD

    locked = as_utc(user.locked_until)
    if locked and locked > utcnow():
        audit_service.log_now(db, action=AuditAction.LOGIN_FAILED, outcome=Outcome.DENIED,
                              user_id=user.id, reason="account locked")
        raise HTTPException(status.HTTP_423_LOCKED, "Account temporarily locked")

    if user.status != "active" or not verify_password(password, user.password_hash):
        user.failed_login_count += 1
        if user.failed_login_count >= settings.max_failed_logins:
            user.locked_until = utcnow() + timedelta(minutes=settings.lockout_minutes)
            user.failed_login_count = 0
        audit_service.log_now(db, action=AuditAction.LOGIN_FAILED, outcome=Outcome.FAILURE,
                              user_id=user.id, reason="bad credentials or inactive")
        raise _BAD

    user.failed_login_count = 0
    user.locked_until = None
    audit_service.log(db, action=AuditAction.LOGIN, outcome=Outcome.SUCCESS, user_id=user.id)
    db.commit()
    return create_access_token(user.id, user.role)


def create_user(db: Session, *, email: str, password: str, full_name: str, role,
                patient_id=None) -> User:
    email = email.strip().lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already in use")
    user = User(email=email, password_hash=hash_password(password), full_name=full_name,
                role=role, patient_id=patient_id)
    db.add(user)
    db.flush()
    return user
