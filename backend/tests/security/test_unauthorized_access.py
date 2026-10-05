from tests.conftest import login, patient_payload

API = "/api/v1"


def _checked_in(client):
    rec = login(client, "reception.a@healthlink.test")
    pid = client.post(f"{API}/patients", json=patient_payload(7), headers=rec).json()["patient"]["id"]
    enc = client.post(f"{API}/encounters/check-in", headers=rec,
                      json={"patient_id": pid, "reason": "Cough"}).json()
    return rec, pid, enc


def test_requires_authentication(client):
    assert client.get(f"{API}/auth/me").status_code == 401


def test_receptionist_cannot_read_clinical_data(client):
    rec, pid, _ = _checked_in(client)
    assert client.get(f"{API}/patients/{pid}/medical-record", headers=rec).status_code == 403


def test_admins_cannot_read_clinical_or_identity_data(client):
    _, pid, _ = _checked_in(client)
    for email in ("admin.a@healthlink.test", "sysadmin@healthlink.test"):
        h = login(client, email)
        assert client.get(f"{API}/patients/{pid}/medical-record", headers=h).status_code == 403
        assert client.get(f"{API}/patients/{pid}", headers=h).status_code == 403


def test_doctor_at_other_facility_denied_and_denial_audited(client):
    _, pid, enc = _checked_in(client)
    doc_b = login(client, "doctor.b@healthlink.test")
    assert client.get(f"{API}/patients/{pid}/medical-record", headers=doc_b).status_code == 403
    assert client.post(f"{API}/encounters/{enc['id']}/start", headers=doc_b).status_code == 404
    mine = client.get(f"{API}/audit/my-access", headers=doc_b).json()
    assert any(a["outcome"] == "denied" for a in mine)


def test_nurse_cannot_prescribe(client):
    rec, pid, enc = _checked_in(client)
    nurse = login(client, "nurse.a@healthlink.test")
    client.post(f"{API}/encounters/{enc['id']}/start", headers=nurse)
    r = client.post(f"{API}/encounters/{enc['id']}/medications", headers=nurse,
                    json={"medication_name": "X", "dosage": "1", "frequency": "daily"})
    assert r.status_code == 403


def test_account_lockout(client):
    for _ in range(5):
        client.post(f"{API}/auth/login", json={"email": "doctor.a@healthlink.test", "password": "wrong"})
    r = client.post(f"{API}/auth/login", json={"email": "doctor.a@healthlink.test",
                                               "password": "Passw0rd!dev"})
    assert r.status_code == 423
