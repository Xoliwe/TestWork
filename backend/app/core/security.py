import hashlib
import secrets
import uuid
from datetime import timedelta

import bcrypt
import jwt

from app.config import settings
from app.db.base import utcnow
from app.models.role import Role


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


# A real hash to compare against when the email is unknown (keeps timing similar).
DUMMY_HASH = hash_password("not-a-real-password")


def create_access_token(user_id: uuid.UUID, role: Role) -> str:
    now = utcnow()
    payload = {"sub": str(user_id), "role": role.value, "iat": now, "jti": uuid.uuid4().hex,
               "exp": now + timedelta(minutes=settings.access_token_minutes)}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


# ---- QR tokens: opaque, random, stored only as a hash ----
def new_qr_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
