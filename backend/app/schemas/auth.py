import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.role import Role


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    full_name: str
    role: Role
    patient_id: uuid.UUID | None = None


class MeOut(UserOut):
    facility_id: uuid.UUID | None = None
    practitioner_id: uuid.UUID | None = None


class StaffCreate(BaseModel):
    email: str
    full_name: str
    password: str = Field(min_length=10)
    role: Role
    facility_id: uuid.UUID
    professional_role: str | None = None


class PatientAccountCreate(BaseModel):
    patient_id: uuid.UUID
    email: str
    password: str = Field(min_length=10)


class FacilityCreate(BaseModel):
    name: str
    facility_type: str
    address: str | None = None


class FacilityOut(FacilityCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
