import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["AUTO_CREATE_TABLES"] = "false"

import pytest
from fastapi.testclient import TestClient

import app.models  # noqa: F401,E402
from app.db.base import Base  # noqa: E402
from app.db.seed import DEV_PASSWORD, seed, synthetic_sa_id  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        seed(s)
    with TestClient(app) as c:
        yield c


def login(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": DEV_PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def patient_payload(seq=1, **over):
    p = {"national_id": synthetic_sa_id("900101", seq), "first_name": "Thandi", "last_name": "Nkosi",
         "date_of_birth": "1990-01-01", "gender": "female", "phone": "0820000000"}
    p.update(over)
    return p
