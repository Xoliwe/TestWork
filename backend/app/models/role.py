import enum


class Role(str, enum.Enum):
    PATIENT = "patient"
    RECEPTIONIST = "receptionist"
    DOCTOR = "doctor"
    NURSE = "nurse"
    FACILITY_ADMIN = "facility_admin"
    SYSTEM_ADMIN = "system_admin"


STAFF_ROLES = {Role.RECEPTIONIST, Role.DOCTOR, Role.NURSE, Role.FACILITY_ADMIN}
CLINICIAN_ROLES = {Role.DOCTOR, Role.NURSE}
