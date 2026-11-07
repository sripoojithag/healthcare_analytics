"""
API Tests: Data Quality API Endpoint
"""
from fastapi.testclient import TestClient
import pytest

from src.api.main import app

client = TestClient(app)


def test_quality_summary_endpoint():
    """Verify data quality summary report endpoint."""
    response = client.get("/api/v1/quality/summary")
    assert response.status_code == 200
    data = response.json()
    assert "dataset_name" in data
    assert "total_records" in data
    assert "overall_completeness_pct" in data
    assert "quality_grade" in data
    assert "validity_checks" in data
