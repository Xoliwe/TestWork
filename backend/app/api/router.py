from fastapi import APIRouter

from app.api.v1 import (audit, auth, checkin, clinical_records, encounters, facilities,
                        patients, staff, users)

api_router = APIRouter()
for r in (auth.router, users.router, facilities.router, staff.router, patients.router,
          checkin.router, encounters.router, clinical_records.router, audit.router):
    api_router.include_router(r)
