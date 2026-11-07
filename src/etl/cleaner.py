"""
Healthcare Data Cleaning & Standardization Module
Applies documented clinical data hygiene rules to the 101,766-encounter dataset.
"""
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd

MEDICATION_COLUMNS = [
    "metformin", "repaglinide", "nateglinide", "chlorpropamide", "glimepiride",
    "acetohexamide", "glipizide", "glyburide", "tolbutamide", "pioglitazone",
    "rosiglitazone", "acarbose", "miglitol", "troglitazone", "tolazamide",
    "examide", "citoglipton", "insulin", "glyburide-metformin",
    "glipizide-metformin", "glimepiride-pioglitazone", "metformin-rosiglitazone",
    "metformin-pioglitazone"
]

NUMERIC_COLUMNS = [
    "time_in_hospital", "num_lab_procedures", "num_procedures", "num_medications",
    "number_outpatient", "number_emergency", "number_inpatient", "number_diagnoses",
    "admission_type_id", "discharge_disposition_id", "admission_source_id"
]


def clean_healthcare_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Clean, standardize, and transform raw healthcare records.
    
    Documented Cleaning Rules:
    1. Replace '?' and blank sentinels with NaN.
    2. Impute high-cardinality missing categoricals (payer_code, medical_specialty, race) with 'Unknown'.
    3. Impute diagnostic codes (diag_1, diag_2, diag_3) with 'Unknown'.
    4. Impute lab indicator results (max_glu_serum, A1Cresult) with 'None'.
    5. Convert encounter metrics to non-negative integers.
    6. Ensure medication columns are standardized to ['No', 'Steady', 'Up', 'Down'].
    7. Generate derived readmission analytics flags:
       - readmitted_binary (1 if readmitted at all, 0 if 'NO')
       - readmitted_30d (1 if readmitted < 30 days, 0 otherwise)
    8. Deduplicate on encounter_id by keeping the record with fewest missing values.
    
    Returns:
        Tuple of (cleaned_df, cleaning_metrics_dict)
    """
    cleaned = df.copy()
    initial_rows = len(cleaned)

    # 1. Sentinel replacement
    cleaned.replace(["?", "None", "NULL", "null", ""], np.nan, inplace=True)

    # 2. Duplicate Encounter Handling
    # Check duplicates by encounter_id
    duplicate_encounters = int(cleaned.duplicated(subset=["encounter_id"]).sum())
    if duplicate_encounters > 0:
        # Sort by non-null count descending so we keep the most complete record
        cleaned["_non_nulls"] = cleaned.notna().sum(axis=1)
        cleaned = cleaned.sort_values("_non_nulls", ascending=False).drop_duplicates(
            subset=["encounter_id"], keep="first"
        ).drop(columns=["_non_nulls"])

    # 3. Categorical Imputation
    for cat_col, default_val in [
        ("race", "Unknown"),
        ("gender", "Unknown/Invalid"),
        ("payer_code", "Unknown"),
        ("medical_specialty", "Unknown"),
        ("weight", "Unknown"),
        ("diag_1", "Unknown"),
        ("diag_2", "Unknown"),
        ("diag_3", "Unknown"),
        ("max_glu_serum", "None"),
        ("A1Cresult", "None"),
    ]:
        if cat_col in cleaned.columns:
            cleaned[cat_col] = cleaned[cat_col].fillna(default_val)

    # 4. Numeric conversions with non-negative validation
    for col in NUMERIC_COLUMNS:
        if col in cleaned.columns:
            cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce").fillna(0).astype(int)
            # Clip negative values if any aberrant data exists
            cleaned[col] = cleaned[col].clip(lower=0)

    # 5. Medication standardization
    for med in MEDICATION_COLUMNS:
        if med in cleaned.columns:
            cleaned[med] = cleaned[med].fillna("No")
            # Enforce valid clinical categories
            cleaned[med] = cleaned[med].apply(
                lambda x: x if x in ["No", "Steady", "Up", "Down"] else "No"
            )

    # 6. Readmission flags
    if "readmitted" in cleaned.columns:
        cleaned["readmitted"] = cleaned["readmitted"].fillna("NO")
        # Standardize formatting
        cleaned["readmitted"] = cleaned["readmitted"].astype(str).str.strip()
        cleaned["readmitted_binary"] = cleaned["readmitted"].apply(
            lambda x: 0 if x == "NO" else 1
        )
        cleaned["readmitted_30d"] = cleaned["readmitted"].apply(
            lambda x: 1 if x == "<30" else 0
        )

    cleaning_metrics = {
        "initial_rows": initial_rows,
        "final_rows": len(cleaned),
        "duplicate_encounters_resolved": duplicate_encounters,
        "features_count": len(cleaned.columns),
        "derived_columns_added": ["readmitted_binary", "readmitted_30d"]
    }

    return cleaned, cleaning_metrics
