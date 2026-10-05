from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings

_kwargs = {}
if settings.database_url.startswith("sqlite"):
    _kwargs = {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}

engine = create_engine(settings.database_url, pool_pre_ping=True, **_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
