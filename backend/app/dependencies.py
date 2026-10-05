import uuid
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.facility import Practitioner
from app.models.role import STAFF_ROLES, Role
from app.models.user import User

bearer = HTTPBearer(auto_error=False)


@dataclass
class Actor:
    user: User
    staff: Practitioner | None


def get_actor(creds: HTTPAuthorizationCredentials | None = Depends(bearer),
              db: Session = Depends(get_db)) -> Actor:
    unauth = HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated",
                           headers={"WWW-Authenticate": "Bearer"})
    if creds is None:
        raise unauth
    try:
        payload = decode_access_token(creds.credentials)
        user = db.get(User, uuid.UUID(payload["sub"]))
    except (jwt.PyJWTError, ValueError, KeyError):
        raise unauth
    if user is None or user.status != "active":
        raise unauth
    staff = db.scalar(select(Practitioner).where(Practitioner.user_id == user.id))
    return Actor(user, staff)


def require_roles(*roles: Role):
    """Coarse gate. Fine-grained patient/facility checks happen in authorization_service."""
    def dep(actor: Actor = Depends(get_actor)) -> Actor:
        if actor.user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        if actor.user.role in STAFF_ROLES and (actor.staff is None or actor.staff.status != "active"):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No active facility membership")
        return actor
    return dep
