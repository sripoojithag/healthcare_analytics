"""
API Tests: Encounters Endpoint & De-Identification Masking
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

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)
Base.metadata.create_all(bind=test_engine)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module", autouse=True)
def setup_encounters_data():
    session = TestSession()
    raw_df = pd.DataFrame({
        "encounter_id": [f"ENC{i}" for i in range(1, 11)],
        "patient_nbr": [f"PT8200{i}" for i in range(1, 11)],
        "race": ["Caucasian"] * 10,
        "gender": ["Male", "Female"] * 5,
        "age": ["[60-70)"] * 10,
        "weight": ["?"] * 10,
        "admission_type_id": [1] * 10,
        "discharge_disposition_id": [1] * 10,
        "admission_source_id": [7] * 10,
        "time_in_hospital": [3] * 10,
        "payer_code": ["MC"] * 10,
        "medical_specialty": ["Cardiology"] * 10,
        "num_lab_procedures": [40] * 10,
        "num_procedures": [1] * 10,
        "num_medications": [12] * 10,
        "number_outpatient": [0] * 10,
        "number_emergency": [0] * 10,
        "number_inpatient": [0] * 10,
        "diag_1": ["414"] * 10,
        "diag_2": ["401"] * 10,
        "diag_3": ["Unknown"] * 10,
        "number_diagnoses": [5] * 10,
        "max_glu_serum": ["None"] * 10,
        "A1Cresult": ["None"] * 10,
        "metformin": ["No"] * 10,
        "insulin": ["Steady"] * 10,
        "change": ["No"] * 10,
        "diabetesMed": ["Yes"] * 10,
        "readmitted": ["<30", "NO"] * 5
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


def test_list_encounters_pagination_and_masking():
    """Verify pagination and that patient identifiers are masked."""
    response = client.get("/api/v1/encounters?page=1&page_size=5", headers={"X-User-Role": "analyst"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_records"] == 10
    assert len(data["encounters"]) == 5
    assert data["page"] == 1
    assert data["page_size"] == 5

    # Check masking format: PT-***{suffix}
    first_record = data["encounters"][0]
    assert first_record["masked_patient_nbr"].startswith("PT-***")
    assert first_record["masked_patient_nbr"] == "PT-***0010"


def test_list_encounters_filtering():
    """Verify gender and readmission filters."""
    response = client.get("/api/v1/encounters?gender=Female&readmitted_30d=1", headers={"X-User-Role": "analyst"})
    assert response.status_code == 200
    data = response.json()
    for enc in data["encounters"]:
        assert enc["gender"] == "Female"
        assert enc["readmitted_30d"] == 1
