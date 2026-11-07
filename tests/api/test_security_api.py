"""
Security, RBAC, and Audit Trail API Tests
Tests unauthorized access, role enforcement (Admin, Analyst, Viewer), and audit logging.
"""
import io
import pandas as pd
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.api.deps import get_db_session
from src.warehouse.db import Base
from src.etl.ingestion import EXPECTED_COLUMNS
from src.security.audit import audit_store

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)
Base.metadata.create_all(bind=test_engine)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module", autouse=True)
def setup_security_db():
    def override_get_db():
        s = TestSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db_session] = override_get_db
    yield
    app.dependency_overrides.clear()
    test_engine.dispose()


client = TestClient(app)


def test_audit_logs_restricted_to_admin():
    """Verify viewer and analyst are blocked from accessing audit logs."""
    # Viewer attempt -> 403
    viewer_res = client.get("/api/v1/audit/logs", headers={"X-User-Role": "viewer"})
    assert viewer_res.status_code == 403

    # Analyst attempt -> 403
    analyst_res = client.get("/api/v1/audit/logs", headers={"X-User-Role": "analyst"})
    assert analyst_res.status_code == 403

    # Admin attempt -> 200
    admin_res = client.get("/api/v1/audit/logs", headers={"X-User-Role": "admin"})
    assert admin_res.status_code == 200
    assert isinstance(admin_res.json(), list)


def test_encounters_blocked_for_viewer_allowed_for_analyst():
    """Verify viewer role cannot view encounter records."""
    viewer_res = client.get("/api/v1/encounters", headers={"X-User-Role": "viewer"})
    assert viewer_res.status_code == 403

    analyst_res = client.get("/api/v1/encounters", headers={"X-User-Role": "analyst"})
    assert analyst_res.status_code in [200, 404]


def test_ingestion_upload_restricted_to_admin():
    """Verify non-admin roles cannot upload dataset CSVs."""
    data = {col: ["Unknown"] for col in EXPECTED_COLUMNS}
    data["encounter_id"] = ["9999"]
    data["patient_nbr"] = ["8888"]
    buf = io.BytesIO()
    pd.DataFrame(data).to_csv(buf, index=False)
    buf.seek(0)

    # Analyst blocked -> 403
    res_analyst = client.post(
        "/api/v1/ingestion/upload",
        files={"file": ("batch.csv", buf.getvalue(), "text/csv")},
        headers={"X-User-Role": "analyst"}
    )
    assert res_analyst.status_code == 403

    # Admin allowed -> 200
    res_admin = client.post(
        "/api/v1/ingestion/upload",
        files={"file": ("batch.csv", buf.getvalue(), "text/csv")},
        headers={"X-User-Role": "admin"}
    )
    assert res_admin.status_code == 200


def test_audit_logging_records_events():
    """Verify security decisions generate audit entries."""
    initial_count = len(audit_store.get_logs(limit=100))

    # Trigger a denied request
    client.get("/api/v1/audit/logs", headers={"X-User-Role": "viewer"})

    logs = audit_store.get_logs(limit=100)
    assert len(logs) > initial_count
    latest = logs[0]
    assert latest["status"] == "DENIED"
    assert latest["action"] == "AUTHORIZE"
    assert latest["role"] == "viewer"
