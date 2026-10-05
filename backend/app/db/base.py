import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(dt: datetime | None) -> datetime | None:
    """SQLite drops tzinfo on read; normalise so comparisons work everywhere."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def enum_col(enum_cls):
    return SAEnum(enum_cls, native_enum=False, length=30,
                  values_callable=lambda e: [m.value for m in e])


class Base(DeclarativeBase):
    pass


class IdMixin:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class CreatedMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
