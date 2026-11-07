"""
Integration Tests for Phase 3: Data Warehouse Star Schema & ETL Loading
Tests schema generation, dimension loading, fact relationships, and analytical SQL queries.
"""
import pandas as pd
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.warehouse.db import Base
from src.warehouse.models import DimPatient, DimDiagnosis, DimEncounterContext, FactEncounter
from src.warehouse.loader import load_cleaned_data_to_warehouse, categorize_icd9
from src.etl.cleaner import clean_healthcare_data


@pytest.fixture
def in_memory_db():
    """Create an isolated in-memory SQLite database for integration testing."""
    test_engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    test_engine.dispose()


@pytest.fixture
def sample_cleaned_df():
    """Build a realistic cleaned DataFrame."""
    raw_df = pd.DataFrame({
        "encounter_id": ["E101", "E102", "E103", "E104", "E105"],
        "patient_nbr": ["P501", "P502", "P501", "P503", "P504"],  # P501 has 2 encounters
        "race": ["Caucasian", "AfricanAmerican", "Caucasian", "Hispanic", "Asian"],
        "gender": ["Female", "Male", "Female", "Female", "Male"],
        "age": ["[40-50)", "[60-70)", "[40-50)", "[70-80)", "[80-90)"],
        "weight": ["?", "?", "?", "?", "?"],
        "admission_type_id": [1, 2, 1, 3, 1],
        "discharge_disposition_id": [1, 3, 1, 1, 6],
        "admission_source_id": [7, 7, 1, 7, 7],
        "time_in_hospital": [3, 8, 4, 12, 2],
        "payer_code": ["MC", "MD", "MC", "?", "HM"],
        "medical_specialty": ["Cardiology", "?", "Cardiology", "InternalMedicine", "?"],
        "num_lab_procedures": [42, 68, 35, 75, 20],
        "num_procedures": [1, 2, 0, 3, 0],
        "num_medications": [14, 25, 11, 32, 8],
        "number_outpatient": [0, 1, 0, 2, 0],
        "number_emergency": [0, 0, 0, 1, 0],
        "number_inpatient": [0, 1, 1, 2, 0],
        "diag_1": ["414", "250.02", "428", "486", "250.4"],
        "diag_2": ["401", "414", "414", "250", "401"],
        "diag_3": ["250", "Unknown", "Unknown", "401", "Unknown"],
        "number_diagnoses": [9, 7, 8, 9, 5],
        "max_glu_serum": ["None", ">300", "None", "None", "None"],
        "A1Cresult": [">8", "None", "None", ">7", "None"],
        "metformin": ["No", "Steady", "No", "No", "Steady"],
        "insulin": ["Up", "Down", "Steady", "Up", "No"],
        "change": ["Ch", "Ch", "No", "Ch", "No"],
        "diabetesMed": ["Yes", "Yes", "Yes", "Yes", "Yes"],
        "readmitted": ["<30", ">30", "NO", "<30", "NO"]
    })
    cleaned, _ = clean_healthcare_data(raw_df)
    return cleaned


def test_icd9_categorization():
    """Verify clinical diagnosis mapping logic."""
    assert categorize_icd9("250.02") == "Diabetes"
    assert categorize_icd9("414") == "Circulatory"
    assert categorize_icd9("486") == "Respiratory"
    assert categorize_icd9("540") == "Digestive"
    assert categorize_icd9("599") == "Genitourinary"
    assert categorize_icd9("Unknown") == "Unknown"


def test_warehouse_loader_populates_star_schema(in_memory_db, sample_cleaned_df):
    """Verify dimension deduplication, foreign key wiring, and fact table metrics."""
    metrics = load_cleaned_data_to_warehouse(sample_cleaned_df, in_memory_db)

    # We passed 5 encounters for 4 distinct patients
    assert in_memory_db.query(DimPatient).count() == 4
    assert in_memory_db.query(FactEncounter).count() == 5
    assert in_memory_db.query(DimEncounterContext).count() == 5
    assert in_memory_db.query(DimDiagnosis).count() > 0

    assert metrics["encounters_loaded"] == 5
    assert metrics["patients_loaded"] == 4


def test_warehouse_loader_is_idempotent(in_memory_db, sample_cleaned_df):
    """Verify loading the same records again does not duplicate encounters."""
    load_cleaned_data_to_warehouse(sample_cleaned_df, in_memory_db)
    initial_facts = in_memory_db.query(FactEncounter).count()

    # Re-run loader
    metrics_rerun = load_cleaned_data_to_warehouse(sample_cleaned_df, in_memory_db)
    assert in_memory_db.query(FactEncounter).count() == initial_facts
    assert metrics_rerun["encounters_loaded"] == 0


def test_warehouse_relationship_traversal(in_memory_db, sample_cleaned_df):
    """Verify ORM relationships between Fact and Dimensions."""
    load_cleaned_data_to_warehouse(sample_cleaned_df, in_memory_db)

    fact = in_memory_db.query(FactEncounter).filter_by(encounter_id="E101").first()
    assert fact is not None
    assert fact.patient.patient_nbr == "P501"
    assert fact.patient.gender == "Female"
    assert fact.primary_diagnosis.category == "Circulatory"
    assert fact.context.medical_specialty == "Cardiology"


def test_warehouse_analytics_sql_query(in_memory_db, sample_cleaned_df):
    """Verify SQL analytical queries with joins and window functions execute cleanly."""
    load_cleaned_data_to_warehouse(sample_cleaned_df, in_memory_db)

    # Test readmission by age group
    sql = text("""
        SELECT 
            p.age_group,
            COUNT(f.encounter_key) AS total_encounters,
            SUM(f.readmitted_30d) AS readmitted_30d
        FROM fact_encounter f
        JOIN dim_patient p ON f.patient_key = p.patient_key
        GROUP BY p.age_group
        ORDER BY total_encounters DESC;
    """)
    result = in_memory_db.execute(sql).fetchall()
    assert len(result) > 0

    # Test stay vs readmission
    sql_stay = text("""
        SELECT 
            time_in_hospital,
            COUNT(*) AS cnt,
            SUM(readmitted_30d) AS readmit_cnt
        FROM fact_encounter
        GROUP BY time_in_hospital
        ORDER BY time_in_hospital;
    """)
    stay_res = in_memory_db.execute(sql_stay).fetchall()
    assert len(stay_res) > 0
