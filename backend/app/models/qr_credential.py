import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedMixin, IdMixin, enum_col


class QRStatus(str, enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"


class QRCredential(IdMixin, CreatedMixin, Base):
    """Only the SHA-256 hash of the opaque token is stored; the plaintext is shown once."""
    __tablename__ = "qr_credentials"

    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[QRStatus] = mapped_column(enum_col(QRStatus), default=QRStatus.ACTIVE)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
