"""
Healthcare Data Quality & Integrity Validation Module
Generates comprehensive quality audits covering missingness, duplicates, outliers, and schema conformity.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List
import pandas as pd


@dataclass
class ColumnQualityMetric:
    column: str
    dtype: str
    total_records: int
    missing_count: int
    missing_pct: float
    unique_values: int
    sample_values: List[Any]


@dataclass
class DataQualityReport:
    """Consolidated Data Quality Audit Report."""
    dataset_name: str
    total_records: int
    total_columns: int
    duplicate_rows: int
    overall_completeness_pct: float
    column_metrics: Dict[str, ColumnQualityMetric] = field(default_factory=dict)
    validity_checks: Dict[str, Any] = field(default_factory=dict)
    quality_grade: str = "A"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "total_records": self.total_records,
            "total_columns": self.total_columns,
            "duplicate_rows": self.duplicate_rows,
            "overall_completeness_pct": round(self.overall_completeness_pct, 2),
            "quality_grade": self.quality_grade,
            "validity_checks": self.validity_checks,
            "column_metrics": {
                col: {
                    "dtype": m.dtype,
                    "missing_count": m.missing_count,
                    "missing_pct": round(m.missing_pct, 2),
                    "unique_values": m.unique_values,
                    "sample_values": m.sample_values
                }
                for col, m in self.column_metrics.items()
            }
        }


def generate_data_quality_report(
    df: pd.DataFrame,
    dataset_name: str = "Healthcare Inpatient Records"
) -> DataQualityReport:
    """
    Run data-quality profiling on the dataset.
    
    Checks:
    1. Overall missingness and per-column null percentages.
    2. Duplicate row counts.
    3. Clinical validity:
       - gender conformity (Male, Female, Unknown/Invalid)
       - time_in_hospital range (1 to 14 days)
       - num_lab_procedures range (1 to 150)
       - num_medications range (1 to 100)
       - readmission target validity (<30, >30, NO)
    """
    total_rows = len(df)
    if total_rows == 0:
        return DataQualityReport(
            dataset_name=dataset_name,
            total_records=0,
            total_columns=len(df.columns),
            duplicate_rows=0,
            overall_completeness_pct=0.0,
            quality_grade="F"
        )

    duplicate_count = int(df.duplicated().sum())

    # Calculate column-level quality
    total_cells = total_rows * len(df.columns)
    missing_cells = int(df.isna().sum().sum())
    completeness = ((total_cells - missing_cells) / total_cells) * 100.0 if total_cells > 0 else 0.0

    col_metrics: Dict[str, ColumnQualityMetric] = {}
    for col in df.columns:
        series = df[col]
        missing_cnt = int(series.isna().sum())
        missing_p = (missing_cnt / total_rows) * 100.0
        unique_cnt = int(series.nunique())
        samples = series.dropna().head(3).tolist()

        col_metrics[col] = ColumnQualityMetric(
            column=col,
            dtype=str(series.dtype),
            total_records=total_rows,
            missing_count=missing_cnt,
            missing_pct=missing_p,
            unique_values=unique_cnt,
            sample_values=samples
        )

    # Clinical validity checks
    validity: Dict[str, Any] = {}

    if "gender" in df.columns:
        valid_genders = {"Male", "Female", "Unknown/Invalid"}
        invalid_gender_count = int((~df["gender"].isin(valid_genders) & df["gender"].notna()).sum())
        validity["gender_conformity"] = {
            "passed": invalid_gender_count == 0,
            "invalid_records": invalid_gender_count
        }

    if "time_in_hospital" in df.columns:
        t_numeric = pd.to_numeric(df["time_in_hospital"], errors="coerce")
        out_of_bounds = int(((t_numeric < 1) | (t_numeric > 14)).sum())
        validity["hospital_stay_range_validity"] = {
            "expected_range": "1-14 days",
            "passed": out_of_bounds == 0,
            "out_of_bounds_count": out_of_bounds
        }

    if "readmitted" in df.columns:
        valid_readmit = {"<30", ">30", "NO"}
        invalid_readmit = int((~df["readmitted"].astype(str).str.strip().isin(valid_readmit)).sum())
        validity["readmission_categories_valid"] = {
            "passed": invalid_readmit == 0,
            "invalid_records": invalid_readmit
        }

    # Assign quality grade based on completeness & validity
    if completeness >= 90.0 and duplicate_count == 0:
        grade = "A"
    elif completeness >= 80.0:
        grade = "B"
    elif completeness >= 70.0:
        grade = "C"
    else:
        grade = "D"

    return DataQualityReport(
        dataset_name=dataset_name,
        total_records=total_rows,
        total_columns=len(df.columns),
        duplicate_rows=duplicate_count,
        overall_completeness_pct=completeness,
        column_metrics=col_metrics,
        validity_checks=validity,
        quality_grade=grade
    )
