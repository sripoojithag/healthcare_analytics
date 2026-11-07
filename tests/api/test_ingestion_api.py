"""
API Tests: Ingestion API Endpoint
"""
import io
import pandas as pd
from fastapi.testclient import TestClient
import pytest

from src.api.main import app
from src.etl.ingestion import EXPECTED_COLUMNS

client = TestClient(app)


def test_upload_non_csv_rejected():
    """Verify non-csv file extension is rejected with 400 Bad Request."""
    file_content = b"Some dummy text"
    response = client.post(
        "/api/v1/ingestion/upload",
        files={"file": ("test.txt", file_content, "text/plain")},
        headers={"X-User-Role": "admin"}
    )
    assert response.status_code == 400
    assert "Only .csv files are supported" in response.json()["detail"]


def test_upload_empty_csv_rejected():
    """Verify empty file is rejected."""
    response = client.post(
        "/api/v1/ingestion/upload",
        files={"file": ("empty.csv", b"", "text/csv")},
        headers={"X-User-Role": "admin"}
    )
    assert response.status_code == 400
    assert "Uploaded file is empty" in response.json()["detail"]


def test_upload_valid_csv():
    """Verify valid healthcare CSV upload produces successful ingestion response."""
    data = {col: ["Unknown", "Unknown"] for col in EXPECTED_COLUMNS}
    data["encounter_id"] = ["9001", "9002"]
    data["patient_nbr"] = ["4001", "4002"]
    data["readmitted"] = ["<30", "NO"]
    df = pd.DataFrame(data)

    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)

    response = client.post(
        "/api/v1/ingestion/upload",
        files={"file": ("patients_batch.csv", buf.getvalue(), "text/csv")},
        headers={"X-User-Role": "admin"}
    )
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "SUCCESS"
    assert res["total_records"] == 2
    assert res["valid_records"] == 2
    assert res["rejected_records"] == 0
