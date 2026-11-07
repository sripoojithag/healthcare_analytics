"""
Unit & Integration Tests for Admin Panel and Data Management.
Covers User Management, Safety Guards, CSV Preview & Mapping, Ingestion Modes,
Dataset Deletion, Model Activation, and Audit Logs.
"""

import io
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.api.deps import get_db_session
from src.warehouse.db import Base
from src.security.auth import seed_default_users, hash_password
from src.warehouse.models import User, FactEncounter, DimPatient, ActiveDataset, IngestionJob

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
Base.metadata.create_all(bind=test_engine)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
client = TestClient(app)

ADMIN_HEADERS = {"X-User-Role": "admin"}
ANALYST_HEADERS = {"X-User-Role": "analyst"}
VIEWER_HEADERS = {"X-User-Role": "viewer"}


@pytest.fixture(scope="module", autouse=True)
def setup_admin_data():
    session = TestSession()
    seed_default_users(session)
    session.close()

    def override_get_db():
        s = TestSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db_session] = override_get_db
    yield
    app.dependency_overrides.pop(get_db_session, None)


# --- 1. User Management & Authorization Tests ---

def test_admin_endpoints_blocked_for_non_admins():
    """Verify non-admin users (viewers and analysts) are forbidden from admin endpoints."""
    # Viewer blocked
    resp_viewer = client.get("/api/v1/admin/users", headers=VIEWER_HEADERS)
    assert resp_viewer.status_code == 403

    # Analyst blocked
    resp_analyst = client.get("/api/v1/admin/users", headers=ANALYST_HEADERS)
    assert resp_analyst.status_code == 403


def test_list_users():
    """Verify admin can list all registered users."""
    resp = client.get("/api/v1/admin/users", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    users = resp.json()
    assert len(users) >= 3
    emails = [u["email"] for u in users]
    assert "admin@healthcare.local" in emails
    assert "analyst@healthcare.local" in emails


def test_create_user():
    """Verify admin can create a new user account."""
    payload = {
        "name": "Dr. Sarah Connor",
        "email": "sarah.connor@hospital.org",
        "password": "SecurePassword#2026",
        "role": "analyst"
    }
    resp = client.post("/api/v1/admin/users", json=payload, headers=ADMIN_HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "success"
    assert data["user"]["email"] == "sarah.connor@hospital.org"
    assert data["user"]["role"] == "analyst"

    # Password should be hashed in DB, never plaintext
    session = TestSession()
    db_user = session.query(User).filter(User.email == "sarah.connor@hospital.org").first()
    assert db_user is not None
    assert db_user.hashed_password.startswith("pbkdf2:sha256:")
    assert "SecurePassword#2026" not in db_user.hashed_password
    session.close()


def test_update_user_role():
    """Verify admin can update another user's role."""
    session = TestSession()
    test_u = User(
        name="Role Test User",
        email="role.test@hospital.org",
        hashed_password=hash_password("DummyPass123!"),
        role="viewer",
        status="active"
    )
    session.add(test_u)
    session.commit()
    target_id = test_u.id
    session.close()

    resp = client.put(f"/api/v1/admin/users/{target_id}/role", json={"role": "analyst"}, headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["new_role"] == "analyst"


def test_self_demotion_prevention():
    """Verify admin cannot demote their own account."""
    session = TestSession()
    admin_u = session.query(User).filter(User.email == "admin@healthcare.local").first()
    admin_id = admin_u.id
    session.close()

    # Pass token for this specific admin
    from src.security.auth import create_access_token
    token = create_access_token(user_id=admin_id, email="admin@healthcare.local", role="admin")

    resp = client.put(
        f"/api/v1/admin/users/{admin_id}/role",
        json={"role": "viewer"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 400
    assert "Self-demotion prohibited" in resp.json()["detail"]


def test_last_admin_protection():
    """Verify system prevents deactivating or demoting the last active admin."""
    from src.security.auth import create_access_token
    session = TestSession()
    # Create second admin so admin1 can act on admin2
    admin2 = User(
        name="Admin Secondary",
        email="admin2@healthcare.local",
        hashed_password=hash_password("Admin2Secure#2026"),
        role="admin",
        status="active"
    )
    session.add(admin2)
    session.commit()
    admin2_id = admin2.id

    # Admin 1 (the caller)
    admin1 = session.query(User).filter(User.email == "admin@healthcare.local").first()
    admin1_id = admin1.id
    token_admin1 = create_access_token(user_id=admin1_id, email=admin1.email, role="admin")
    session.close()

    # Step 1: Admin 1 deactivates admin 2 -> succeeds (since admin 1 is still active)
    resp1 = client.put(
        f"/api/v1/admin/users/{admin2_id}/status",
        json={"status": "inactive"},
        headers={"Authorization": f"Bearer {token_admin1}"}
    )
    assert resp1.status_code == 200

    # Step 2: Now only admin1 is active. Admin 2 logs in with token and tries to deactivate admin1 -> rejected as last active administrator
    token_admin2 = create_access_token(user_id=admin2_id, email="admin2@healthcare.local", role="admin")
    resp2 = client.put(
        f"/api/v1/admin/users/{admin1_id}/status",
        json={"status": "inactive"},
        headers={"Authorization": f"Bearer {token_admin2}"}
    )
    assert resp2.status_code == 400
    assert "last active administrator" in resp2.json()["detail"].lower()


def test_reset_user_password():
    """Verify admin can reset user credentials."""
    session = TestSession()
    u = session.query(User).filter(User.email == "sarah.connor@hospital.org").first()
    user_id = u.id
    session.close()

    resp = client.post(
        f"/api/v1/admin/users/{user_id}/reset-password",
        json={"new_password": "BrandNewSecurePassword123#"},
        headers=ADMIN_HEADERS
    )
    assert resp.status_code == 200
    assert "reset successfully" in resp.json()["message"]


# --- 2. Data Management: Preview, Mapping, Append & Replace Tests ---

SAMPLE_CSV = """encounter_id,patient_nbr,race,gender,age,weight,admission_type_id,discharge_disposition_id,admission_source_id,time_in_hospital,payer_code,medical_specialty,num_lab_procedures,num_procedures,num_medications,number_outpatient,number_emergency,number_inpatient,diag_1,diag_2,diag_3,number_diagnoses,max_glu_serum,A1Cresult,metformin,repaglinide,nateglinide,chlorpropamide,glimepiride,acetohexamide,glipizide,glyburide,tolbutamide,pioglitazone,rosiglitazone,acarbose,miglitol,troglitazone,tolazamide,examide,citoglipton,insulin,glyburide-metformin,glipizide-metformin,glimepiride-pioglitazone,metformin-rosiglitazone,metformin-pioglitazone,change,diabetesMed,readmitted
ENC_T1,PT_T1,Caucasian,Female,[50-60),?,1,1,7,3,MC,Cardiology,45,1,12,0,0,0,250.0,414,401,5,None,None,No,No,No,No,No,No,No,No,No,No,No,No,No,No,No,No,No,Steady,No,No,No,No,No,No,Yes,NO
ENC_T2,PT_T2,AfricanAmerican,Male,[60-70),?,2,1,1,6,MD,InternalMedicine,62,2,18,0,0,1,428,250.02,401,7,None,None,Steady,No,No,No,No,No,No,No,No,No,No,No,No,No,No,No,No,No,No,No,No,No,No,No,Yes,<30
"""

def test_dataset_preview():
    """Verify CSV preview validates schema, detects columns, and suggests mappings."""
    files = {"file": ("test_upload.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")}
    resp = client.post("/api/v1/admin/dataset/preview", files=files, headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "test_upload.csv"
    assert data["schema_valid"] is True
    assert len(data["preview_records"]) == 2
    assert "encounter_id" in data["detected_columns"]


def test_dataset_append_mode():
    """Verify Append mode loads valid records and prevents duplicate encounters on re-upload."""
    files = {"file": ("test_append.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")}
    resp = client.post(
        "/api/v1/admin/dataset/ingest",
        files=files,
        data={"mode": "append"},
        headers=ADMIN_HEADERS
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["inserted_records"] == 2
    assert data["duplicate_records"] == 0

    # Re-uploading the exact same file must NOT create duplicates
    files_again = {"file": ("test_append.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")}
    resp_again = client.post(
        "/api/v1/admin/dataset/ingest",
        files=files_again,
        data={"mode": "append"},
        headers=ADMIN_HEADERS
    )
    assert resp_again.status_code == 200
    data_again = resp_again.json()
    assert data_again["inserted_records"] == 0
    assert data_again["duplicate_records"] == 2


def test_dataset_replace_mode():
    """Verify Replace mode replaces existing active data after explicit confirmation."""
    REPLACE_CSV = """encounter_id,patient_nbr,race,gender,age,weight,admission_type_id,discharge_disposition_id,admission_source_id,time_in_hospital,payer_code,medical_specialty,num_lab_procedures,num_procedures,num_medications,number_outpatient,number_emergency,number_inpatient,diag_1,diag_2,diag_3,number_diagnoses,max_glu_serum,A1Cresult,metformin,repaglinide,nateglinide,chlorpropamide,glimepiride,acetohexamide,glipizide,glyburide,tolbutamide,pioglitazone,rosiglitazone,acarbose,miglitol,troglitazone,tolazamide,examide,citoglipton,insulin,glyburide-metformin,glipizide-metformin,glimepiride-pioglitazone,metformin-rosiglitazone,metformin-pioglitazone,change,diabetesMed,readmitted
ENC_REPLACE_1,PT_R1,Caucasian,Female,[70-80),?,1,1,7,4,MC,Cardiology,50,1,10,0,0,0,250.0,414,401,5,None,None,No,No,No,No,No,No,No,No,No,No,No,No,No,No,No,No,No,Steady,No,No,No,No,No,No,Yes,NO
"""
    # 1. Missing confirmation -> 400
    files = {"file": ("test_replace.csv", REPLACE_CSV.encode("utf-8"), "text/csv")}
    resp_no_confirm = client.post(
        "/api/v1/admin/dataset/ingest",
        files=files,
        data={"mode": "replace", "confirm_replace": "false"},
        headers=ADMIN_HEADERS
    )
    assert resp_no_confirm.status_code == 400

    # 2. With confirmation -> Replace succeeds
    files2 = {"file": ("test_replace.csv", REPLACE_CSV.encode("utf-8"), "text/csv")}
    resp_confirm = client.post(
        "/api/v1/admin/dataset/ingest",
        files=files2,
        data={"mode": "replace", "confirm_replace": "true"},
        headers=ADMIN_HEADERS
    )
    assert resp_confirm.status_code == 200
    res_data = resp_confirm.json()
    assert res_data["mode"] == "replace"
    assert res_data["total_active_records"] == 1


# --- 3. Data Deletion & Empty Analytics Tests ---

def test_delete_active_dataset_requires_confirmation_phrase():
    """Verify deletion requires exact phrase 'DELETE ACTIVE DATASET'."""
    resp = client.post(
        "/api/v1/admin/dataset/delete",
        json={"confirmation_phrase": "please delete"},
        headers=ADMIN_HEADERS
    )
    assert resp.status_code == 400
    assert "Confirmation phrase mismatch" in resp.json()["detail"]


def test_delete_active_dataset_execution_and_empty_analytics():
    """Verify active records are deleted while preserving history, and analytics returns empty state."""
    resp = client.post(
        "/api/v1/admin/dataset/delete",
        json={"confirmation_phrase": "DELETE ACTIVE DATASET"},
        headers=ADMIN_HEADERS
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    # Verify warehouse encounters is 0
    session = TestSession()
    assert session.query(FactEncounter).count() == 0
    # Ingestion history remains intact
    assert session.query(IngestionJob).count() > 0
    session.close()

    # Verify analytics returns clean empty state without dividing by zero
    kpi_resp = client.get("/api/v1/analytics/kpis")
    assert kpi_resp.status_code == 200
    kpi_data = kpi_resp.json()
    assert kpi_data["total_encounters"] == 0
    assert kpi_data["readmitted_30d_rate_pct"] == 0.0

    age_resp = client.get("/api/v1/analytics/readmissions-by-age")
    assert age_resp.status_code == 200
    assert age_resp.json() == []


# --- 4. Model Management & Audit Logs Tests ---

def test_list_and_activate_models():
    """Verify admin can inspect available models and activate an artifact."""
    resp_list = client.get("/api/v1/admin/models", headers=ADMIN_HEADERS)
    assert resp_list.status_code == 200
    models = resp_list.json()
    assert len(models) > 0
    assert any(m["name"] == "readmission_pipeline_v1.joblib" for m in models)

    # Activate
    resp_act = client.post(
        "/api/v1/admin/models/activate",
        json={"model_name": "readmission_pipeline_v1.joblib"},
        headers=ADMIN_HEADERS
    )
    assert resp_act.status_code == 200
    assert resp_act.json()["active_model"] == "readmission_pipeline_v1.joblib"


def test_audit_logs_and_system_status():
    """Verify audit logs record administrative events and system status reports health."""
    resp_audit = client.get("/api/v1/admin/audit-logs", headers=ADMIN_HEADERS)
    assert resp_audit.status_code == 200
    logs = resp_audit.json()
    assert len(logs) > 0
    actions = [l["action"] for l in logs]
    assert any("DATASET" in a or "USER" in a or "MODEL" in a for a in actions)

    resp_status = client.get("/api/v1/admin/system-status", headers=ADMIN_HEADERS)
    assert resp_status.status_code == 200
    status_data = resp_status.json()
    assert status_data["status"] in ["healthy", "degraded"]
    assert "services" in status_data
    assert "warehouse_db" in status_data["services"]
