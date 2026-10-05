# Import every model so Base.metadata (and Alembic autogenerate) sees them.
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.clinical_record import (Allergy, ClinicalRecord, Diagnosis,  # noqa: F401
                                        LabResult, Medication)
from app.models.consent import Consent  # noqa: F401
from app.models.encounter import Encounter  # noqa: F401
from app.models.facility import Facility, Practitioner  # noqa: F401
from app.models.patient import Patient  # noqa: F401
from app.models.qr_credential import QRCredential  # noqa: F401
from app.models.user import User  # noqa: F401
