import enum

from app.models.role import Role


class Category(str, enum.Enum):
    IDENTITY = "identity"
    ADMINISTRATIVE = "administrative"
    CLINICAL = "clinical"


# What each role may ever see about a patient. Admins deliberately get nothing.
ROLE_CATEGORIES: dict[Role, set[Category]] = {
    Role.RECEPTIONIST: {Category.IDENTITY, Category.ADMINISTRATIVE},
    Role.DOCTOR: {Category.IDENTITY, Category.ADMINISTRATIVE, Category.CLINICAL},
    Role.NURSE: {Category.IDENTITY, Category.ADMINISTRATIVE, Category.CLINICAL},
    Role.FACILITY_ADMIN: set(),
    Role.SYSTEM_ADMIN: set(),
}
