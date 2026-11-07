"""
Unit Tests for Data Quality Reporting Module
"""
import pandas as pd
import pytest

from src.etl.data_quality import generate_data_quality_report, DataQualityReport


def test_data_quality_report_empty_df():
    """Verify quality report handles empty DataFrame gracefully."""
    empty_df = pd.DataFrame(columns=["encounter_id", "patient_nbr"])
    report = generate_data_quality_report(empty_df)
    assert report.total_records == 0
    assert report.quality_grade == "F"
    assert report.overall_completeness_pct == 0.0


def test_data_quality_report_metrics_and_validity():
    """Verify missingness metrics and validity checks."""
    df = pd.DataFrame({
        "encounter_id": ["E1", "E2", "E3", "E4"],
        "gender": ["Male", "Female", "InvalidGender", "Male"],
        "time_in_hospital": [4, 15, 2, 7],  # 15 is out of bounds (1-14)
        "readmitted": ["<30", "NO", ">30", "UNKNOWN_VAL"],  # UNKNOWN_VAL is invalid
        "payer_code": ["MC", None, "MD", None]  # 50% missing
    })

    report = generate_data_quality_report(df)
    assert report.total_records == 4
    assert report.total_columns == 5
    assert report.duplicate_rows == 0

    # Payer code missingness
    payer_metrics = report.column_metrics["payer_code"]
    assert payer_metrics.missing_count == 2
    assert payer_metrics.missing_pct == 50.0

    # Validity checks
    assert report.validity_checks["gender_conformity"]["passed"] is False
    assert report.validity_checks["gender_conformity"]["invalid_records"] == 1

    assert report.validity_checks["hospital_stay_range_validity"]["passed"] is False
    assert report.validity_checks["hospital_stay_range_validity"]["out_of_bounds_count"] == 1

    assert report.validity_checks["readmission_categories_valid"]["passed"] is False
    assert report.validity_checks["readmission_categories_valid"]["invalid_records"] == 1

    # Check serialization
    d = report.to_dict()
    assert "overall_completeness_pct" in d
    assert "quality_grade" in d
    assert "column_metrics" in d
