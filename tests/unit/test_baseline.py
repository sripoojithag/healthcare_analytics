"""
Phase 1: Baseline & Repository Audit Tests
Validates the structural baseline, existing datasets, SQL assets, and original artifacts.
"""
import os
import csv
import json
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

EXPECTED_RAW_COLUMNS = [
    "encounter_id", "patient_nbr", "race", "gender", "age", "weight",
    "admission_type_id", "discharge_disposition_id", "admission_source_id",
    "time_in_hospital", "payer_code", "medical_specialty", "num_lab_procedures",
    "num_procedures", "num_medications", "number_outpatient", "number_emergency",
    "number_inpatient", "diag_1", "diag_2", "diag_3", "number_diagnoses",
    "max_glu_serum", "A1Cresult", "metformin", "repaglinide", "nateglinide",
    "chlorpropamide", "glimepiride", "acetohexamide", "glipizide", "glyburide",
    "tolbutamide", "pioglitazone", "rosiglitazone", "acarbose", "miglitol",
    "troglitazone", "tolazamide", "examide", "citoglipton", "insulin",
    "glyburide-metformin", "glipizide-metformin", "glimepiride-pioglitazone",
    "metformin-rosiglitazone", "metformin-pioglitazone", "change", "diabetesMed",
    "readmitted"
]


def test_existing_datasets_present():
    """Verify raw and preprocessed CSV datasets exist in data/."""
    raw_path = os.path.join(BASE_DIR, "data", "diabetic_data.csv")
    cleaned_path = os.path.join(BASE_DIR, "data", "cleaned_healthcare_data.csv")
    final_path = os.path.join(BASE_DIR, "data", "final_healthcare_analysis.csv")

    assert os.path.exists(raw_path), f"Missing raw dataset: {raw_path}"
    assert os.path.exists(cleaned_path), f"Missing cleaned dataset: {cleaned_path}"
    assert os.path.exists(final_path), f"Missing final dataset: {final_path}"


def test_raw_dataset_schema():
    """Verify that diabetic_data.csv has all 50 expected clinical & encounter columns."""
    raw_path = os.path.join(BASE_DIR, "data", "diabetic_data.csv")
    with open(raw_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert len(header) == 50, f"Expected 50 columns, found {len(header)}"
        assert header == EXPECTED_RAW_COLUMNS, "Raw dataset columns do not match expected schema"


def test_sql_queries_exist_and_valid():
    """Verify analytics_queries.sql exists and contains key analytical queries."""
    sql_path = os.path.join(BASE_DIR, "sql", "analytics_queries.sql")
    assert os.path.exists(sql_path), f"Missing SQL file: {sql_path}"

    with open(sql_path, mode="r", encoding="utf-8") as f:
        content = f.read()

    assert "SELECT COUNT(*) AS total_patients" in content
    assert "SUM(readmitted = '<30')" in content
    assert "RANK() OVER" in content
    assert "time_in_hospital" in content


def test_notebook_structure_valid():
    """Verify notebooks/healthcare_analysis.ipynb exists and is valid JSON."""
    nb_path = os.path.join(BASE_DIR, "notebooks", "healthcare_analysis.ipynb")
    assert os.path.exists(nb_path), f"Missing notebook: {nb_path}"

    with open(nb_path, mode="r", encoding="utf-8") as f:
        data = json.load(f)

    assert "cells" in data
    assert len(data["cells"]) > 0, "Notebook has no cells"


def test_dashboard_and_streamlit_preserved():
    """Verify existing Power BI pbix and Streamlit application.py exist."""
    pbix_path = os.path.join(BASE_DIR, "dashboard", "healthcare_dashboard.pbix")
    app_path = os.path.join(BASE_DIR, "app", "application.py")

    assert os.path.exists(pbix_path), f"Missing Power BI dashboard: {pbix_path}"
    assert os.path.exists(app_path), f"Missing Streamlit app: {app_path}"

    with open(app_path, mode="r", encoding="utf-8") as f:
        streamlit_code = f.read()
    assert "streamlit as st" in streamlit_code
