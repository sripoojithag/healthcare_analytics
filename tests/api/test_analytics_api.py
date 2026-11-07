"""
API Tests: Analytics & KPI Endpoints
"""
import pandas as pd
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.api.deps import get_db_session
from src.warehouse.db import Base
from src.warehouse.loader import load_cleaned_data_to_warehouse
from src.etl.cleaner import clean_healthcare_data

# Create isolated test database shared across threads using StaticPool
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)
Base.metadata.create_all(bind=test_engine)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module", autouse=True)
def seed_test_database():
    """Seed test database with known encounters for API tests."""
    session = TestSession()
    raw_df = pd.DataFrame({
        "encounter_id": ["E1", "E2", "E3", "E4"],
        "patient_nbr": ["P1", "P2", "P3", "P4"],
        "race": ["Caucasian", "AfricanAmerican", "Hispanic", "Asian"],
        "gender": ["Female", "Male", "Female", "Male"],
        "age": ["[40-50)", "[60-70)", "[70-80)", "[80-90)"],
        "weight": ["?", "?", "?", "?"],
        "admission_type_id": [1, 2, 1, 3],
        "discharge_disposition_id": [1, 1, 1, 1],
        "admission_source_id": [7, 7, 7, 7],
        "time_in_hospital": [2, 5, 8, 14],
        "payer_code": ["MC", "MD", "HM", "MC"],
        "medical_specialty": ["Cardiology", "InternalMedicine", "Surgery", "Pediatrics"],
        "num_lab_procedures": [20, 45, 60, 80],
        "num_procedures": [0, 1, 2, 3],
        "num_medications": [8, 15, 24, 35],
        "number_outpatient": [0, 0, 1, 0],
        "number_emergency": [0, 0, 0, 1],
        "number_inpatient": [0, 1, 0, 2],
        "diag_1": ["414", "250", "486", "540"],
        "diag_2": ["401", "414", "250", "Unknown"],
        "diag_3": ["Unknown", "Unknown", "Unknown", "Unknown"],
        "number_diagnoses": [5, 6, 7, 8],
        "max_glu_serum": ["None", "None", ">200", "None"],
        "A1Cresult": ["None", ">7", ">8", "None"],
        "metformin": ["No", "Steady", "No", "Up"],
        "insulin": ["No", "Steady", "Up", "Down"],
        "change": ["No", "Ch", "Ch", "Ch"],
        "diabetesMed": ["No", "Yes", "Yes", "Yes"],
        "readmitted": ["NO", ">30", "<30", "<30"]
    })
    cleaned, _ = clean_healthcare_data(raw_df)
    load_cleaned_data_to_warehouse(cleaned, session)
    session.close()

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


def test_get_kpis():
    """Verify macro KPI calculations."""
    response = client.get("/api/v1/analytics/kpis")
    assert response.status_code == 200
    data = response.json()
    assert data["total_encounters"] == 4
    assert data["unique_patients"] == 4
    assert data["readmitted_30d_count"] == 2  # E3 & E4
    assert data["readmitted_30d_rate_pct"] == 50.0
    assert data["total_readmissions_count"] == 3  # E2, E3, E4
    assert data["avg_length_of_stay_days"] > 0


def test_get_kpis_with_gender_filter():
    """Verify gender filter in KPIs."""
    response = client.get("/api/v1/analytics/kpis?gender=Female")
    assert response.status_code == 200
    data = response.json()
    assert data["total_encounters"] == 2


def test_get_readmissions_by_age():
    """Verify readmission rates stratified by age."""
    response = client.get("/api/v1/analytics/readmissions-by-age")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "age_group" in data[0]
    assert "readmission_30d_pct" in data[0]


def test_get_stay_vs_readmission():
    """Verify stay correlation endpoint."""
    response = client.get("/api/v1/analytics/stay-vs-readmission")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "stay_days" in data[0]
    assert "readmission_30d_rate_pct" in data[0]


def test_get_medications_impact():
    """Verify polypharmacy impact endpoint."""
    response = client.get("/api/v1/analytics/medications-impact")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "medication_tier" in data[0]


def test_predict_readmission_api():
    """Verify POST /api/v1/analytics/predict endpoint."""
    payload = {
        "time_in_hospital": 4,
        "num_lab_procedures": 45,
        "num_procedures": 1,
        "num_medications": 14,
        "age": "[60-70)",
        "gender": "Female",
        "race": "Caucasian",
        "insulin": "Steady",
        "diabetesMed": "Yes"
    }
    response = client.post("/api/v1/analytics/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "readmission_probability" in data
    assert 0.0 <= data["readmission_probability"] <= 1.0
    assert data["predicted_class"] in [0, 1]
    assert data["risk_tier"] in ["Low Risk", "Medium Risk", "High Risk"]
    assert "recommendation" in data

