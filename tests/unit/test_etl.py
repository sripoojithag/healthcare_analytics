"""
Unit Tests for Phase 2: Ingestion & Cleaner Modules
Tests valid data, invalid data, missing columns, deduplication, and edge cases.
"""
import io
import os
import pandas as pd
import pytest

from src.etl.ingestion import ingest_csv, validate_schema, EXPECTED_COLUMNS
from src.etl.cleaner import clean_healthcare_data


@pytest.fixture
def sample_valid_csv():
    """Build a minimal valid CSV payload containing all 50 required columns."""
    data = {col: ["Unknown", "Unknown", "Unknown"] for col in EXPECTED_COLUMNS}
    data["encounter_id"] = ["1001", "1002", "1003"]
    data["patient_nbr"] = ["5001", "5002", "5003"]
    data["race"] = ["Caucasian", "AfricanAmerican", "?"]
    data["gender"] = ["Female", "Male", "Unknown/Invalid"]
    data["age"] = ["[40-50)", "[60-70)", "[70-80)"]
    data["time_in_hospital"] = ["3", "7", "1"]
    data["num_lab_procedures"] = ["40", "65", "12"]
    data["num_medications"] = ["15", "22", "6"]
    data["readmitted"] = ["<30", ">30", "NO"]
    df = pd.DataFrame(data)
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    csv_buf.seek(0)
    return csv_buf


def test_validate_schema_exact():
    """Verify schema validator recognizes complete 50-attribute header."""
    res = validate_schema(EXPECTED_COLUMNS)
    assert len(res["missing"]) == 0
    assert len(res["unexpected"]) == 0


def test_validate_schema_missing_columns():
    """Verify schema validator detects missing columns."""
    incomplete_cols = EXPECTED_COLUMNS[:30]
    res = validate_schema(incomplete_cols)
    assert len(res["missing"]) == 20
    assert "readmitted" in res["missing"]


def test_ingest_valid_csv_stream(sample_valid_csv):
    """Verify successful ingestion of valid stream."""
    result = ingest_csv(sample_valid_csv)
    assert result.status == "SUCCESS"
    assert result.total_records == 3
    assert result.valid_records == 3
    assert result.rejected_records == 0
    assert len(result.errors) == 0


def test_ingest_missing_mandatory_identifiers():
    """Verify rejection when encounter_id or patient_nbr is absent."""
    df = pd.DataFrame({"age": ["[50-60)"], "gender": ["Male"]})
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)

    result = ingest_csv(buf)
    assert result.status == "FAILED"
    assert any("critical identifier" in err for err in result.errors)


def test_ingest_rejects_empty_identifiers():
    """Verify rows with blank encounter_id or patient_nbr are rejected."""
    data = {col: ["Unknown", "Unknown"] for col in EXPECTED_COLUMNS}
    data["encounter_id"] = ["101", ""]  # second row has blank encounter_id
    data["patient_nbr"] = ["201", "202"]
    df = pd.DataFrame(data)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)

    result = ingest_csv(buf)
    assert result.status == "PARTIAL"
    assert result.valid_records == 1
    assert result.rejected_records == 1


def test_cleaner_handles_sentinels_and_duplicates():
    """Test cleaner replaces sentinels with NaN/defaults and resolves duplicate encounter IDs."""
    raw_df = pd.DataFrame({
        "encounter_id": ["E1", "E1", "E2"],
        "patient_nbr": ["P1", "P1", "P2"],
        "race": ["?", "Caucasian", "Asian"],
        "gender": ["Male", "Male", "Female"],
        "payer_code": ["?", "MC", "?"],
        "medical_specialty": ["?", "Cardiology", "?"],
        "weight": ["?", "?", "?"],
        "time_in_hospital": ["4", "4", "2"],
        "num_lab_procedures": ["30", "30", "15"],
        "num_medications": ["12", "12", "5"],
        "readmitted": ["<30", "<30", "NO"]
    })

    cleaned, metrics = clean_healthcare_data(raw_df)

    # Duplicate E1 should be deduplicated to 1 record, keeping the more complete row
    assert len(cleaned) == 2
    assert metrics["duplicate_encounters_resolved"] == 1
    assert cleaned.loc[cleaned["encounter_id"] == "E1", "race"].values[0] == "Caucasian"
    assert cleaned.loc[cleaned["encounter_id"] == "E1", "payer_code"].values[0] == "MC"


def test_cleaner_generates_readmission_binary_flags():
    """Test readmitted_binary and readmitted_30d derivations."""
    raw_df = pd.DataFrame({
        "encounter_id": ["E1", "E2", "E3"],
        "patient_nbr": ["P1", "P2", "P3"],
        "readmitted": ["<30", ">30", "NO"]
    })
    cleaned, _ = clean_healthcare_data(raw_df)

    assert list(cleaned["readmitted_binary"]) == [1, 1, 0]
    assert list(cleaned["readmitted_30d"]) == [1, 0, 0]


def test_cleaner_numeric_sanitization():
    """Test numeric values conversion and clipping negatives."""
    raw_df = pd.DataFrame({
        "encounter_id": ["E1", "E2"],
        "patient_nbr": ["P1", "P2"],
        "time_in_hospital": ["5", "-2"],
        "num_lab_procedures": ["45", "invalid_num"]
    })
    cleaned, _ = clean_healthcare_data(raw_df)

    # -2 should be clipped to 0, invalid_num should be imputed to 0
    assert cleaned.loc[cleaned["encounter_id"] == "E2", "time_in_hospital"].values[0] == 0
    assert cleaned.loc[cleaned["encounter_id"] == "E2", "num_lab_procedures"].values[0] == 0
