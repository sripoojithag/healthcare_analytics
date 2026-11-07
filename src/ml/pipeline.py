"""
Healthcare Readmission Machine Learning Pipeline
Leak-free training, comprehensive evaluation (Precision, Recall, F1, ROC-AUC), and inference engine.
"""
from typing import Dict, Any, Tuple, Optional, List
import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.etl.cleaner import clean_healthcare_data

NUMERIC_FEATURES = [
    "time_in_hospital",
    "num_lab_procedures",
    "num_procedures",
    "num_medications",
    "number_outpatient",
    "number_emergency",
    "number_inpatient",
    "number_diagnoses"
]

CATEGORICAL_FEATURES = [
    "age",
    "gender",
    "race",
    "insulin",
    "diabetesMed"
]

DEFAULT_MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../models"))
DEFAULT_MODEL_PATH = os.path.join(DEFAULT_MODEL_DIR, "readmission_pipeline_v1.joblib")
DEFAULT_METADATA_PATH = os.path.join(DEFAULT_MODEL_DIR, "model_metadata.json")


def build_pipeline() -> Pipeline:
    """Build leak-free Scikit-learn preprocessing and Random Forest pipeline."""
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES)
        ]
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=10,
                class_weight="balanced",
                random_state=42
            ))
        ]
    )
    return pipeline


def evaluate_pipeline(
    pipeline: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Dict[str, Any]:
    """
    Evaluate trained model using classification metrics beyond simple accuracy.
    Includes precision, recall, F1, ROC-AUC, and confusion matrix.
    """
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp)
        }
    }
    return metrics


def train_and_save_pipeline(
    data_path: str,
    output_model_path: str = DEFAULT_MODEL_PATH,
    output_metadata_path: str = DEFAULT_METADATA_PATH,
    sample_size: Optional[int] = 10000
) -> Tuple[Pipeline, Dict[str, Any]]:
    """
    Train model, evaluate metrics, and serialize artifacts to disk.
    
    Args:
        data_path: Path to raw or cleaned dataset CSV.
        output_model_path: Target joblib file path.
        output_metadata_path: Target metadata json path.
        sample_size: Optional sample limit for fast reproducible training.
    """
    os.makedirs(os.path.dirname(output_model_path), exist_ok=True)
    df = pd.read_csv(data_path, nrows=sample_size)
    cleaned, _ = clean_healthcare_data(df)

    # Feature matrix X and target y
    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    X = cleaned[features]
    y = cleaned["readmitted_binary"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    metrics = evaluate_pipeline(pipeline, X_test, y_test)

    # Serialize trained pipeline artifact
    joblib.dump(pipeline, output_model_path)

    metadata = {
        "model_version": "v1.0.0",
        "algorithm": "RandomForestClassifier(n_estimators=100, max_depth=10)",
        "features": {
            "numeric": NUMERIC_FEATURES,
            "categorical": CATEGORICAL_FEATURES
        },
        "target": "readmitted_binary",
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "metrics": metrics
    }

    with open(output_metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return pipeline, metadata


def load_pipeline(model_path: str = DEFAULT_MODEL_PATH) -> Pipeline:
    """Load serialized pipeline from disk."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model artifact not found at {model_path}")
    return joblib.load(model_path)


def predict_readmission_risk(
    patient_data: Dict[str, Any],
    model: Optional[Pipeline] = None,
    model_path: str = DEFAULT_MODEL_PATH
) -> Dict[str, Any]:
    """
    Perform real inference using the trained Scikit-learn pipeline.
    
    Returns:
        Dict with predicted_class (0 or 1), readmission_probability (0.0 to 1.0),
        and clinical risk_tier ('Low Risk', 'Medium Risk', 'High Risk').
    """
    if model is None:
        model = load_pipeline(model_path)

    # Validate and build 1-row DataFrame
    record = {}
    for col in NUMERIC_FEATURES:
        val = patient_data.get(col, 0)
        try:
            record[col] = [max(0, int(val))]
        except (ValueError, TypeError):
            record[col] = [0]

    for col in CATEGORICAL_FEATURES:
        val = patient_data.get(col, "Unknown")
        record[col] = [str(val).strip()]

    input_df = pd.DataFrame(record)

    prob = float(model.predict_proba(input_df)[0][1])
    pred_class = int(prob >= 0.5)

    if prob > 0.70:
        tier = "High Risk"
    elif prob > 0.40:
        tier = "Medium Risk"
    else:
        tier = "Low Risk"

    return {
        "readmission_probability": round(prob, 4),
        "predicted_class": pred_class,
        "risk_tier": tier,
        "recommendation": (
            "Flag for intensive post-discharge telemedicine and nurse follow-up within 48 hours."
            if tier == "High Risk" else
            "Schedule follow-up appointment within 7-14 days and review medication adherence."
            if tier == "Medium Risk" else
            "Standard routine outpatient follow-up care."
        )
    }
