"""
Unit Tests for Phase 5: Machine Learning Pipeline
Tests leak-free preprocessing, model loading, comprehensive metrics, and inference.
"""
import os
import pytest
import pandas as pd
from src.ml.pipeline import (
    build_pipeline, evaluate_pipeline, load_pipeline,
    predict_readmission_risk, DEFAULT_MODEL_PATH, DEFAULT_METADATA_PATH,
    NUMERIC_FEATURES, CATEGORICAL_FEATURES
)


def test_build_pipeline_structure():
    """Verify ColumnTransformer and Random Forest components in pipeline."""
    pipe = build_pipeline()
    assert "preprocessor" in pipe.named_steps
    assert "classifier" in pipe.named_steps


def test_model_artifact_exists_and_loads():
    """Verify the saved joblib model artifact loads successfully."""
    assert os.path.exists(DEFAULT_MODEL_PATH), "Model artifact does not exist on disk"
    pipe = load_pipeline(DEFAULT_MODEL_PATH)
    assert pipe is not None


def test_predict_readmission_risk_valid():
    """Verify prediction function returns probability, class, tier, and recommendation."""
    patient = {
        "time_in_hospital": 5,
        "num_lab_procedures": 50,
        "num_procedures": 2,
        "num_medications": 18,
        "number_outpatient": 0,
        "number_emergency": 0,
        "number_inpatient": 1,
        "number_diagnoses": 8,
        "age": "[60-70)",
        "gender": "Female",
        "race": "Caucasian",
        "insulin": "Up",
        "diabetesMed": "Yes"
    }

    res = predict_readmission_risk(patient)
    assert "readmission_probability" in res
    assert 0.0 <= res["readmission_probability"] <= 1.0
    assert res["predicted_class"] in [0, 1]
    assert res["risk_tier"] in ["Low Risk", "Medium Risk", "High Risk"]
    assert "recommendation" in res
    assert len(res["recommendation"]) > 10


def test_predict_readmission_risk_edge_cases():
    """Verify inference pipeline handles empty/missing fields and negative numbers without crashing."""
    corrupted_patient = {
        "time_in_hospital": -5,  # negative should be clamped to 0
        "num_lab_procedures": "invalid_val",  # string should be coerced to 0
        "gender": "NonBinary",  # unseen category should be handled smoothly by OneHotEncoder
        "age": "Centenarian"
    }

    res = predict_readmission_risk(corrupted_patient)
    assert "readmission_probability" in res
    assert 0.0 <= res["readmission_probability"] <= 1.0
    assert res["risk_tier"] in ["Low Risk", "Medium Risk", "High Risk"]


def test_evaluate_pipeline_metrics():
    """Verify evaluation generates precision, recall, f1, roc-auc, and confusion matrix."""
    pipe = build_pipeline()
    # Create small synthetic test data
    X = pd.DataFrame({
        "time_in_hospital": [2, 8, 3, 10],
        "num_lab_procedures": [20, 60, 30, 80],
        "num_procedures": [0, 2, 1, 3],
        "num_medications": [5, 25, 10, 30],
        "number_outpatient": [0, 0, 1, 0],
        "number_emergency": [0, 0, 0, 1],
        "number_inpatient": [0, 1, 0, 2],
        "number_diagnoses": [4, 8, 5, 9],
        "age": ["[40-50)", "[70-80)", "[50-60)", "[80-90)"],
        "gender": ["Female", "Male", "Female", "Male"],
        "race": ["Caucasian", "AfricanAmerican", "Hispanic", "Asian"],
        "insulin": ["No", "Up", "Steady", "Down"],
        "diabetesMed": ["No", "Yes", "Yes", "Yes"]
    })
    y = pd.Series([0, 1, 0, 1])
    pipe.fit(X, y)

    metrics = evaluate_pipeline(pipe, X, y)
    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert "roc_auc" in metrics
    assert "confusion_matrix" in metrics
    assert "true_positives" in metrics["confusion_matrix"]
