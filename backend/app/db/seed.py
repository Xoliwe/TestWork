"""Synthetic data only. Run: python -m app.db.seed"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.facility import Facility, Practitioner
from app.models.role import Role
from app.models.user import User
from app.schemas.patient import luhn_check_digit

DEV_PASSWORD = "Passw0rd!dev"


def synthetic_sa_id(yymmdd: str, seq: int) -> str:
    first12 = f"{yymmdd}{5000 + seq:04d}08"  # 08 = citizenship/race digits (legacy), fixed
    return first12 + luhn_check_digit(first12)


def seed(db: Session) -> dict:
    if db.scalar(select(User.id).limit(1)):
        return {}
    pw = hash_password(DEV_PASSWORD)
    fac_a = Facility(name="Cape Town Community Clinic", facility_type="clinic")
    fac_b = Facility(name="Groote Schuur Demo Hospital", facility_type="hospital")
    db.add_all([fac_a, fac_b])
    db.flush()

    def user(email, name, role, fac=None, prof=None):
        u = User(email=email, password_hash=pw, full_name=name, role=role)
        db.add(u)
        db.flush()
        if fac:
            db.add(Practitioner(user_id=u.id, facility_id=fac.id, professional_role=prof or role.value))
        return u

    user("sysadmin@healthlink.test", "System Admin", Role.SYSTEM_ADMIN)
    user("admin.a@healthlink.test", "Alice Admin (A)", Role.FACILITY_ADMIN, fac_a)
    user("reception.a@healthlink.test", "Rita Reception (A)", Role.RECEPTIONIST, fac_a)
    user("doctor.a@healthlink.test", "Dr Dumisani (A)", Role.DOCTOR, fac_a, "general practitioner")
    user("nurse.a@healthlink.test", "Nurse Naledi (A)", Role.NURSE, fac_a)
    user("reception.b@healthlink.test", "Ben Reception (B)", Role.RECEPTIONIST, fac_b)
    user("doctor.b@healthlink.test", "Dr Botha (B)", Role.DOCTOR, fac_b, "physician")
    db.commit()
    return {"password": DEV_PASSWORD, "facility_a": str(fac_a.id), "facility_b": str(fac_b.id)}


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        info = seed(s)
    print("Seeded." if info else "Already seeded.", info)
    print("Sample valid synthetic SA IDs:", synthetic_sa_id("900101", 1), synthetic_sa_id("851231", 2))
