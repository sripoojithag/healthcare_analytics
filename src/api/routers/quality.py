"""
Data Quality Reporting Router
"""
import os
from fastapi import APIRouter, Depends, HTTPException
import pandas as pd

from src.api.schemas import DataQualitySummaryResponse
from src.etl.data_quality import generate_data_quality_report

router = APIRouter(prefix="/quality", tags=["Data Quality"])

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/diabetic_data.csv"))


@router.get("/summary", response_model=DataQualitySummaryResponse)
def get_data_quality_summary():
    """Retrieve comprehensive data-quality profiling report."""
    if not os.path.exists(DATA_PATH):
        raise HTTPException(status_code=404, detail="Primary dataset not found on disk.")

    # Read sample (or full dataset) for quality report
    df = pd.read_csv(DATA_PATH, nrows=5000)
    report = generate_data_quality_report(df, dataset_name="UCI Diabetes 130-US Hospitals (Sample)")

    return DataQualitySummaryResponse(
        dataset_name=report.dataset_name,
        total_records=report.total_records,
        total_columns=report.total_columns,
        duplicate_rows=report.duplicate_rows,
        overall_completeness_pct=round(report.overall_completeness_pct, 2),
        quality_grade=report.quality_grade,
        validity_checks=report.validity_checks
    )
