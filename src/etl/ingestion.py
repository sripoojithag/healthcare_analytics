"""
Healthcare Data Ingestion & Schema Validation Module

Responsibilities:
1. Read healthcare CSV files.
2. Normalize incoming column names.
3. Map supported aliases to the canonical UCI Diabetes schema.
4. Validate the expected 50-column schema.
5. Validate mandatory identifiers.
6. Reject rows with missing identifiers.
7. Return a structured ingestion report.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
import io
import os

import pandas as pd


# ============================================================
# 1. CANONICAL SCHEMA
# ============================================================

# Exact 50 raw columns from the UCI Diabetes dataset.

EXPECTED_COLUMNS: List[str] = [
    "encounter_id", "patient_nbr", "race", "gender", "age", "weight",
    "admission_type_id", "discharge_disposition_id", "admission_source_id",
    "time_in_hospital", "payer_code", "medical_specialty",
    "num_lab_procedures", "num_procedures", "num_medications",
    "number_outpatient", "number_emergency", "number_inpatient",
    "diag_1", "diag_2", "diag_3", "number_diagnoses",
    "max_glu_serum", "A1Cresult", "metformin", "repaglinide",
    "nateglinide", "chlorpropamide", "glimepiride", "acetohexamide",
    "glipizide", "glyburide", "tolbutamide", "pioglitazone",
    "rosiglitazone", "acarbose", "miglitol", "troglitazone",
    "tolazamide", "examide", "citoglipton", "insulin",
    "glyburide-metformin", "glipizide-metformin",
    "glimepiride-pioglitazone", "metformin-rosiglitazone",
    "metformin-pioglitazone", "change", "diabetesMed", "readmitted"
]


# These identifiers are mandatory for each encounter.

MANDATORY_IDENTIFIERS = [
    "encounter_id",
    "patient_nbr"
]


# ============================================================
# 2. COLUMN ALIAS CONFIGURATION
# ============================================================

# Format:
# "canonical database column": ["possible incoming names"]

COLUMN_ALIASES: Dict[str, List[str]] = {

    "encounter_id": [
        "visit_id",
        "encounter",
        "visit_number"
    ],

    "patient_nbr": [
        "patient_id",
        "patient_number"
    ],

    "gender": [
        "sex"
    ],

    "time_in_hospital": [
        "length_of_stay",
        "hospital_stay_days"
    ],

    "num_medications": [
        "medication_count",
        "num_meds"
    ],

    "number_outpatient": [
        "outpatient_visits"
    ],

    "number_emergency": [
        "emergency_visits"
    ],

    "number_inpatient": [
        "inpatient_visits"
    ],

    "readmitted": [
        "readmission_status"
    ]
}


# ============================================================
# 3. INGESTION RESULT
# ============================================================

@dataclass
class IngestionResult:
    """Structured report of a CSV ingestion operation."""

    status: str

    total_records: int = 0
    valid_records: int = 0
    rejected_records: int = 0

    missing_columns: List[str] = field(default_factory=list)
    unexpected_columns: List[str] = field(default_factory=list)

    # Source column -> canonical column
    mapped_columns: Dict[str, str] = field(default_factory=dict)

    errors: List[str] = field(default_factory=list)

    data: Optional[pd.DataFrame] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert ingestion result into a JSON-friendly report."""

        return {
            "status": self.status,
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "rejected_records": self.rejected_records,
            "missing_columns": self.missing_columns,
            "unexpected_columns": self.unexpected_columns,
            "mapped_columns": self.mapped_columns,
            "errors": self.errors
        }


# ============================================================
# 4. HEADER NORMALIZATION
# ============================================================

def normalize_header(name: str) -> str:
    """
    Normalize column headers for comparison.

    Examples:
        Patient ID       -> patient_id
        PATIENT-ID       -> patient_id
        patient_nbr      -> patient_nbr

    Canonical output names are preserved separately.
    """

    return (
        str(name)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


# ============================================================
# 5. COLUMN MAPPING
# ============================================================

def map_schema_columns(
    df: pd.DataFrame
) -> tuple[pd.DataFrame, Dict[str, str]]:
    """
    Map incoming column names to the canonical UCI schema.

    Returns:
        mapped_df:
            DataFrame with standardized column names.

        mapped_columns:
            Dictionary containing source -> canonical names.
    """

    df = df.copy()

    # Step 1: Normalize incoming headers.

    normalized_headers = {}

    for original_name in df.columns:

        normalized_name = normalize_header(original_name)

        if normalized_name in normalized_headers:

            raise ValueError(
                f"Duplicate headers after normalization: "
                f"'{original_name}'"
            )

        normalized_headers[normalized_name] = original_name

    # Step 2: Create canonical column lookup.

    canonical_lookup = {
        normalize_header(column): column
        for column in EXPECTED_COLUMNS
    }

    # Step 3: Add supported aliases.

    for canonical_name, aliases in COLUMN_ALIASES.items():

        for alias in aliases:

            normalized_alias = normalize_header(alias)

            if normalized_alias in canonical_lookup:

                raise ValueError(
                    f"Alias '{alias}' conflicts with "
                    f"an existing canonical column."
                )

            canonical_lookup[normalized_alias] = canonical_name

    # Step 4: Build rename dictionary.

    rename_map = {}

    for normalized_name, original_name in normalized_headers.items():

        canonical_name = canonical_lookup.get(normalized_name)

        if canonical_name is not None:

            rename_map[original_name] = canonical_name

    # Step 5: Prevent two source columns from mapping
    # to the same canonical destination.

    destinations = list(rename_map.values())

    if len(destinations) != len(set(destinations)):

        raise ValueError(
            "Multiple incoming columns map to the same "
            "canonical column. Please resolve the ambiguity."
        )

    # Step 6: Rename columns.

    mapped_df = df.rename(columns=rename_map)

    # Step 7: Record only actual renames.

    mapped_columns = {
        source: destination
        for source, destination in rename_map.items()
        if source != destination
    }

    return mapped_df, mapped_columns


# ============================================================
# 6. SCHEMA VALIDATION
# ============================================================

def validate_schema(
    columns: List[str]
) -> Dict[str, List[str]]:
    """
    Compare incoming columns against the expected 50-column schema.

    Returns:
        missing: Expected columns not present.
        unexpected: Incoming columns not recognized.
    """

    cols_set = set(columns)
    expected_set = set(EXPECTED_COLUMNS)

    missing = [
        column
        for column in EXPECTED_COLUMNS
        if column not in cols_set
    ]

    unexpected = [
        column
        for column in columns
        if column not in expected_set
    ]

    return {
        "missing": missing,
        "unexpected": unexpected
    }


# ============================================================
# 7. CSV INGESTION
# ============================================================

def ingest_csv(
    source: Union[str, io.StringIO, io.BytesIO],
    nrows: Optional[int] = None
) -> IngestionResult:
    """
    Read, map and validate an incoming healthcare CSV.

    Args:
        source:
            CSV file path, StringIO buffer or BytesIO buffer.

        nrows:
            Optional number of rows to read.

    Returns:
        IngestionResult containing validation report and valid data.
    """

    # --------------------------------------------------------
    # Step 1: Validate file path and extension.
    # --------------------------------------------------------

    if isinstance(source, str):

        if not os.path.exists(source):

            return IngestionResult(
                status="FAILED",
                errors=[f"File not found: {source}"]
            )

        if not source.lower().endswith(".csv"):

            return IngestionResult(
                status="FAILED",
                errors=[
                    f"Invalid file extension: {source}. "
                    "Expected .csv"
                ]
            )

    # --------------------------------------------------------
    # Step 2: Read CSV.
    # --------------------------------------------------------

    try:

        df = pd.read_csv(
            source,
            nrows=nrows,
            dtype=str
        )

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

    total_records = len(df)

    # --------------------------------------------------------
    # Step 3: Map incoming columns.
    # --------------------------------------------------------

    try:

        df, mapped_columns = map_schema_columns(df)

    except ValueError as e:

        return IngestionResult(
            status="FAILED",
            total_records=total_records,
            errors=[f"Column mapping failed: {str(e)}"]
        )

    # --------------------------------------------------------
    # Step 4: Validate the mapped schema.
    # --------------------------------------------------------

    schema_diff = validate_schema(
        list(df.columns)
    )

    missing_cols = schema_diff["missing"]
    unexpected_cols = schema_diff["unexpected"]

    # --------------------------------------------------------
    # Step 5: Check mandatory identifiers.
    # --------------------------------------------------------

    missing_mandatory = [
        column
        for column in MANDATORY_IDENTIFIERS
        if column in missing_cols
    ]

    if missing_mandatory:

        return IngestionResult(
            status="FAILED",
            total_records=total_records,
            missing_columns=missing_cols,
            unexpected_columns=unexpected_cols,
            mapped_columns=mapped_columns,
            errors=[
                "Missing critical identifier columns: "
                f"{missing_mandatory}"
            ]
        )

    # --------------------------------------------------------
    # Step 6: Reject rows with missing mandatory identifiers.
    # --------------------------------------------------------

    invalid_mask = (
        df["encounter_id"].isna()
        | (df["encounter_id"].str.strip() == "")
        | df["patient_nbr"].isna()
        | (df["patient_nbr"].str.strip() == "")
    )

    rejected_count = int(invalid_mask.sum())

    valid_df = df.loc[~invalid_mask].copy()

    valid_count = len(valid_df)

    # --------------------------------------------------------
    # Step 7: Determine ingestion status.
    # --------------------------------------------------------

    if valid_count == 0:

        status = "FAILED"

    elif (
        missing_cols
        or unexpected_cols
        or rejected_count > 0
    ):

        status = "PARTIAL"

    else:

        status = "SUCCESS"

    # --------------------------------------------------------
    # Step 8: Prepare ingestion messages.
    # --------------------------------------------------------

    errors = []

    if missing_cols:

        errors.append(
            f"{len(missing_cols)} expected columns are missing."
        )

    if unexpected_cols:

        errors.append(
            f"{len(unexpected_cols)} unrecognized columns found."
        )

    if rejected_count > 0:

        errors.append(
            f"{rejected_count} rows rejected due to "
            "missing mandatory identifiers."
        )

    # --------------------------------------------------------
    # Step 9: Return structured result.
    # --------------------------------------------------------

    return IngestionResult(
        status=status,
        total_records=total_records,
        valid_records=valid_count,
        rejected_records=rejected_count,
        missing_columns=missing_cols,
        unexpected_columns=unexpected_cols,
        mapped_columns=mapped_columns,
        errors=errors,
        data=valid_df
    )
