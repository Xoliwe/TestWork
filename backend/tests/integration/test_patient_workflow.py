"""The MVP journey from the spec, end to end."""
from tests.conftest import login, patient_payload

API = "/api/v1"


def register(client, h, seq=1):
    r = client.post(f"{API}/patients", json=patient_payload(seq), headers=h)
    assert r.status_code == 201, r.text
    return r.json()


def test_full_mvp_journey(client):
    rec = login(client, "reception.a@healthlink.test")
    doc = login(client, "doctor.a@healthlink.test")

    reg = register(client, rec)
    pid, token = reg["patient"]["id"], reg["qr_token"]
    assert reg["patient"]["healthlink_id"].startswith("HL-")
    assert reg["patient"]["national_id_masked"].startswith("*********")

    # QR is opaque: contains no national ID / name.
    assert reg["patient"]["first_name"] not in token

    # Returning patient: reception scans QR and checks in
    scan = client.post(f"{API}/qr/resolve", json={"qr_token": token}, headers=rec).json()
    assert scan["patient_id"] == pid and scan["active_encounter_id"] is None
    enc = client.post(f"{API}/encounters/check-in", headers=rec,
                      json={"patient_id": pid, "reason": "Headache"}).json()
    assert enc["status"] == "checked_in" and enc["practitioner_id"] is None

    # Doctor cannot read clinical data until they take the patient? Encounter is open => allowed (read).
    waiting = client.get(f"{API}/encounters/waiting", headers=doc).json()
    assert len(waiting) == 1

    # Writing requires consultation started
    r = client.post(f"{API}/encounters/{enc['id']}/notes", headers=doc,
                    json={"content": "Tension headache"})
    assert r.status_code == 409

    started = client.post(f"{API}/encounters/{enc['id']}/start", headers=doc).json()
    assert started["status"] == "in_consultation" and started["practitioner_id"]

    assert client.post(f"{API}/encounters/{enc['id']}/notes", headers=doc,
                       json={"content": "Tension headache"}).status_code == 201
    assert client.post(f"{API}/encounters/{enc['id']}/diagnoses", headers=doc,
                       json={"code": "G44.2", "description": "Tension-type headache"}).status_code == 201
    assert client.post(f"{API}/encounters/{enc['id']}/medications", headers=doc,
                       json={"medication_name": "Paracetamol", "dosage": "500mg",
                             "frequency": "6-hourly"}).status_code == 201

    mr = client.get(f"{API}/patients/{pid}/medical-record", headers=doc).json()
    assert len(mr["diagnoses"]) == 1 and len(mr["medications"]) == 1
    assert mr["other_facilities_included"] is False

    assert client.post(f"{API}/encounters/{enc['id']}/checkout", headers=doc).json()["status"] == "completed"

    # After checkout, clinical access closes
    assert client.get(f"{API}/patients/{pid}/medical-record", headers=doc).status_code == 403

    # Patient account sees own record and who accessed it
    assert client.post(f"{API}/users/patient-account", headers=rec, json={
        "patient_id": pid, "email": "thandi@healthlink.test", "password": "Passw0rd!dev"}).status_code == 201
    pat = login(client, "thandi@healthlink.test")
    assert client.get(f"{API}/patients/{pid}/medical-record", headers=pat).status_code == 200
    actions = {a["action"] for a in client.get(f"{API}/audit/my-access", headers=pat).json()}
    assert {"VIEW_PATIENT_RECORD", "PATIENT_CHECK_IN"} <= actions


def test_duplicate_registration_blocked(client):
    rec = login(client, "reception.a@healthlink.test")
    first = register(client, rec)
    r = client.post(f"{API}/patients", json=patient_payload(1), headers=rec)
    assert r.status_code == 409
    assert r.json()["healthlink_id"] == first["patient"]["healthlink_id"]


def test_invalid_sa_id_rejected(client):
    rec = login(client, "reception.a@healthlink.test")
    r = client.post(f"{API}/patients", json=patient_payload(1, national_id="1234567890123"), headers=rec)
    assert r.status_code == 422


def test_reissued_qr_revokes_old_one(client):
    rec = login(client, "reception.a@healthlink.test")
    reg = register(client, rec)
    new = client.post(f"{API}/patients/{reg['patient']['id']}/qr/reissue", headers=rec).json()["qr_token"]
    assert client.post(f"{API}/qr/resolve", json={"qr_token": reg["qr_token"]}, headers=rec).status_code == 404
    assert client.post(f"{API}/qr/resolve", json={"qr_token": new}, headers=rec).status_code == 200
