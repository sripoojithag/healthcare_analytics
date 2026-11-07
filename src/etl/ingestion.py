"""
Healthcare Data Ingestion & Schema Validation Module
Validates file formats, schemas, and required columns according to the 50-attribute UCI Diabetes dataset.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
import io
import os
import pandas as pd

# The exact 50 raw columns from diabetic_data.csv
EXPECTED_COLUMNS: List[str] = [
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

MANDATORY_IDENTIFIERS: List[str] = ["encounter_id", "patient_nbr"]


@dataclass
class IngestionResult:
    """Structured report of an ingestion run."""
    status: str  # "SUCCESS", "PARTIAL", "FAILED"
    total_records: int = 0
    valid_records: int = 0
    rejected_records: int = 0
    missing_columns: List[str] = field(default_factory=list)
    unexpected_columns: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    data: Optional[pd.DataFrame] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "rejected_records": self.rejected_records,
            "missing_columns": self.missing_columns,
            "unexpected_columns": self.unexpected_columns,
            "errors": self.errors
        }


def validate_schema(columns: List[str]) -> Dict[str, List[str]]:
    """Check columns against the expected 50-attribute schema."""
    cols_set = set(columns)
    expected_set = set(EXPECTED_COLUMNS)

    missing = [c for c in EXPECTED_COLUMNS if c not in cols_set]
    unexpected = [c for c in columns if c not in expected_set]
    return {"missing": missing, "unexpected": unexpected}


def ingest_csv(
    source: Union[str, io.StringIO, io.BytesIO],
    nrows: Optional[int] = None
) -> IngestionResult:
    """
    Ingest healthcare CSV file or buffer and validate schema.
    
    Args:
        source: File path, string buffer, or bytes buffer
        nrows: Optional row limit for sampling/testing
        
    Returns:
        IngestionResult with status, validation errors, and DataFrame if valid.
    """
    if isinstance(source, str):
        if not os.path.exists(source):
            return IngestionResult(
                status="FAILED",
                errors=[f"File not found: {source}"]
            )
        if not source.endswith(".csv"):
            return IngestionResult(
                status="FAILED",
                errors=[f"Invalid file extension: {source}. Expected .csv"]
            )

    try:
        df = pd.read_csv(source, nrows=nrows, dtype=str)
    except Exception as e:
        return IngestionResult(
            status="FAILED",
            errors=[f"Failed to parse CSV: {str(e)}"]
        )

    if df.empty:
        return IngestionResult(
            status="FAILED",
            total_records=0,
            errors=["Uploaded file is empty (0 records)."]
        )

    # Schema validation
    schema_diff = validate_schema(list(df.columns))
    missing_cols = schema_diff["missing"]
    unexpected_cols = schema_diff["unexpected"]

    # Check mandatory identifier columns
    missing_mandatory = [c for c in MANDATORY_IDENTIFIERS if c in missing_cols]
    if missing_mandatory:
        return IngestionResult(
            status="FAILED",
            total_records=len(df),
            missing_columns=missing_cols,
            unexpected_columns=unexpected_cols,
            errors=[f"Missing critical identifier columns: {missing_mandatory}"]
        )

    # Reject rows with missing or blank mandatory IDs
    invalid_mask = df["encounter_id"].isna() | (df["encounter_id"].str.strip() == "") | \
                   df["patient_nbr"].isna() | (df["patient_nbr"].str.strip() == "")
    
    rejected_count = int(invalid_mask.sum())
    valid_df = df[~invalid_mask].copy()

    status = "SUCCESS" if (not missing_cols and rejected_count == 0) else "PARTIAL" if len(valid_df) > 0 else "FAILED"

    errors = []
    if missing_cols:
        errors.append(f"{len(missing_cols)} optional columns missing from schema.")
    if rejected_count > 0:
        errors.append(f"{rejected_count} rows rejected due to missing mandatory identifiers.")

    return IngestionResult(
        status=status,
        total_records=len(df),
        valid_records=len(valid_df),
        rejected_records=rejected_count,
        missing_columns=missing_cols,
        unexpected_columns=unexpected_cols,
        errors=errors,
        data=valid_df
    )
