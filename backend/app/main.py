from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.models  # noqa: F401  (register tables)
from app.api.router import api_router
from app.config import settings
from app.core.exceptions import DuplicatePatientError
from app.core.middleware import SecurityHeadersMiddleware
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        Base.metadata.create_all(engine)
    yield


app = FastAPI(title="HealthLink API", version="0.1.0", lifespan=lifespan)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","),
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(DuplicatePatientError)
async def duplicate_patient(_: Request, exc: DuplicatePatientError):
    return JSONResponse(status_code=409, content={
        "detail": "Patient profile already exists.", "healthlink_id": exc.healthlink_id})


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(api_router, prefix="/api/v1")
