import re
import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


def luhn_check_digit(first12: str) -> str:
    total = 0
    for i, ch in enumerate(reversed(first12)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return str((10 - total % 10) % 10)


def valid_sa_id(v: str) -> bool:
    if not re.fullmatch(r"\d{13}", v):
        return False
    if not (1 <= int(v[2:4]) <= 12 and 1 <= int(v[4:6]) <= 31):
        return False
    return luhn_check_digit(v[:12]) == v[12]


class PatientCreate(BaseModel):
    national_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Literal["male", "female", "other", "unknown"]
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None

    @field_validator("national_id")
    @classmethod
    def _check_id(cls, v: str) -> str:
        v = v.strip()
        if not valid_sa_id(v):
            raise ValueError("Invalid South African ID number")
        return v


class PatientIdentityOut(BaseModel):
    """Identity view. National ID is always masked in responses."""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    healthlink_id: str
    national_id_masked: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class PatientRegistrationOut(BaseModel):
    patient: PatientIdentityOut
    qr_token: str  # shown ONCE; frontend renders it as a QR code / prints the card


class QRResolveRequest(BaseModel):
    qr_token: str


class QRResolveOut(BaseModel):
    patient_id: uuid.UUID
    healthlink_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    national_id_masked: str
    active_encounter_id: uuid.UUID | None = None
    active_encounter_status: str | None = None
