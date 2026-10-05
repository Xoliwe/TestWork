import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, utcnow

CROSS_FACILITY_PURPOSE = "cross_facility_sharing"


class Consent(IdMixin, Base):
    __tablename__ = "consents"
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="granted")  # granted | revoked
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
