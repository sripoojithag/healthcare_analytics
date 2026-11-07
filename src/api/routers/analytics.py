"""
Analytics & KPI Endpoints Powered by the Star Schema Warehouse
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.deps import get_db_session
from src.api.schemas import (
    KPIResponse, AgeCohortMetric, StayCorrelationMetric,
    DiagnosisRiskMetric, MedicationImpactMetric,
    PredictionRequest, PredictionResponse
)
from src.warehouse.models import FactEncounter, DimPatient
from src.ml.pipeline import predict_readmission_risk

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/kpis", response_model=KPIResponse)
def get_warehouse_kpis(
    gender: Optional[str] = Query(None, description="Filter by gender: Male, Female"),
    db: Session = Depends(get_db_session)
):
    """Retrieve macro-level clinical and readmission KPIs from the warehouse."""
    sql = """
        SELECT 
            COUNT(f.encounter_key) AS total_encounters,
            COUNT(DISTINCT f.patient_key) AS unique_patients,
            COALESCE(SUM(f.readmitted_30d), 0) AS readmitted_30d_count,
            COALESCE(SUM(f.readmitted_binary), 0) AS total_readmissions_count,
            COALESCE(AVG(f.time_in_hospital), 0) AS avg_length_of_stay,
            COALESCE(AVG(f.num_lab_procedures), 0) AS avg_labs,
            COALESCE(AVG(f.num_medications), 0) AS avg_meds
        FROM fact_encounter f
        JOIN dim_patient p ON f.patient_key = p.patient_key
        WHERE (:gender IS NULL OR p.gender = :gender)
    """
    row = db.execute(text(sql), {"gender": gender}).fetchone()
    if not row or row[0] == 0:
        return KPIResponse(
            total_encounters=0,
            unique_patients=0,
            readmitted_30d_count=0,
            readmitted_30d_rate_pct=0.0,
            total_readmissions_count=0,
            total_readmission_rate_pct=0.0,
            avg_length_of_stay_days=0.0,
            avg_lab_procedures=0.0,
            avg_medications_per_encounter=0.0
        )

    tot = row[0]
    readmit_30d = row[2]
    readmit_tot = row[3]

    return KPIResponse(
        total_encounters=tot,
        unique_patients=row[1],
        readmitted_30d_count=readmit_30d,
        readmitted_30d_rate_pct=round((readmit_30d / tot) * 100.0, 2),
        total_readmissions_count=readmit_tot,
        total_readmission_rate_pct=round((readmit_tot / tot) * 100.0, 2),
        avg_length_of_stay_days=round(float(row[4]), 2),
        avg_lab_procedures=round(float(row[5]), 2),
        avg_medications_per_encounter=round(float(row[6]), 2)
    )


@router.get("/readmissions-by-age", response_model=List[AgeCohortMetric])
def get_readmissions_by_age(db: Session = Depends(get_db_session)):
    """Retrieve 30-day readmission distribution stratified by age cohorts."""
    sql = """
        SELECT 
            p.age_group,
            COUNT(f.encounter_key) AS total_encounters,
            COUNT(DISTINCT p.patient_key) AS unique_patients,
            COALESCE(SUM(f.readmitted_30d), 0) AS readmitted_30d,
            COALESCE(AVG(f.time_in_hospital), 0) AS avg_stay,
            COALESCE(AVG(f.num_medications), 0) AS avg_meds
        FROM fact_encounter f
        JOIN dim_patient p ON f.patient_key = p.patient_key
        GROUP BY p.age_group
        ORDER BY total_encounters DESC
    """
    rows = db.execute(text(sql)).fetchall()
    results = []
    for r in rows:
        tot = r[1]
        r30 = r[3]
        pct = round((r30 / tot) * 100.0, 2) if tot > 0 else 0.0
        results.append(AgeCohortMetric(
            age_group=r[0] or "Unknown",
            total_encounters=tot,
            unique_patients=r[2],
            readmitted_30d=r30,
            readmission_30d_pct=pct,
            avg_hospital_stay=round(float(r[4]), 2),
            avg_medications=round(float(r[5]), 2)
        ))
    return results


@router.get("/stay-vs-readmission", response_model=List[StayCorrelationMetric])
def get_stay_vs_readmission(db: Session = Depends(get_db_session)):
    """Analyze length of hospital stay vs. readmission rate."""
    sql = """
        SELECT 
            f.time_in_hospital AS stay_days,
            COUNT(f.encounter_key) AS total_patients,
            COALESCE(SUM(f.readmitted_30d), 0) AS readmitted_30d,
            COALESCE(AVG(f.num_lab_procedures), 0) AS avg_labs,
            COALESCE(AVG(f.num_medications), 0) AS avg_meds
        FROM fact_encounter f
        GROUP BY f.time_in_hospital
        ORDER BY stay_days ASC
    """
    rows = db.execute(text(sql)).fetchall()
    results = []
    for r in rows:
        tot = r[1]
        r30 = r[2]
        pct = round((r30 / tot) * 100.0, 2) if tot > 0 else 0.0
        results.append(StayCorrelationMetric(
            stay_days=r[0],
            total_patients=tot,
            readmitted_30d=r30,
            readmission_30d_rate_pct=pct,
            avg_labs=round(float(r[3]), 2),
            avg_meds=round(float(r[4]), 2)
        ))
    return results


@router.get("/diagnosis-risk", response_model=List[DiagnosisRiskMetric])
def get_diagnosis_risk_rankings(db: Session = Depends(get_db_session)):
    """Retrieve disease categories ranked by 30-day readmission risk using window functions."""
    sql = """
        WITH DiagStats AS (
            SELECT 
                d.category AS diagnosis_category,
                COUNT(f.encounter_key) AS encounters,
                COALESCE(SUM(f.readmitted_30d), 0) AS readmissions_under_30,
                COALESCE(AVG(f.time_in_hospital), 0) AS avg_stay
            FROM fact_encounter f
            JOIN dim_diagnosis d ON f.primary_diag_key = d.diagnosis_key
            GROUP BY d.category
        )
        SELECT 
            diagnosis_category,
            encounters,
            readmissions_under_30,
            ROUND((CAST(readmissions_under_30 AS FLOAT) / encounters) * 100.0, 2) AS readmission_rate_pct,
            ROUND(avg_stay, 2) AS avg_length_of_stay,
            RANK() OVER (ORDER BY (CAST(readmissions_under_30 AS FLOAT) / encounters) DESC) AS risk_rank
        FROM DiagStats
        ORDER BY risk_rank ASC
    """
    try:
        rows = db.execute(text(sql)).fetchall()
        return [
            DiagnosisRiskMetric(
                diagnosis_category=r[0],
                encounters=r[1],
                readmissions_under_30=r[2],
                readmission_rate_pct=float(r[3]),
                avg_length_of_stay=float(r[4]),
                risk_rank=int(r[5])
            )
            for r in rows
        ]
    except Exception:
        return []


@router.get("/medications-impact", response_model=List[MedicationImpactMetric])
def get_medications_impact(db: Session = Depends(get_db_session)):
    """Analyze how polypharmacy and insulin administration influence readmission risk."""
    sql = """
        WITH MedTiers AS (
            SELECT 
                encounter_key,
                readmitted_30d,
                insulin,
                CASE 
                    WHEN num_medications <= 10 THEN 'Low (1-10 meds)'
                    WHEN num_medications <= 20 THEN 'Moderate (11-20 meds)'
                    WHEN num_medications <= 30 THEN 'High (21-30 meds)'
                    ELSE 'Severe Polypharmacy (31+ meds)'
                END AS medication_tier
            FROM fact_encounter
        )
        SELECT 
            medication_tier,
            insulin,
            COUNT(*) AS encounter_count,
            COALESCE(SUM(readmitted_30d), 0) AS readmissions_30d
        FROM MedTiers
        GROUP BY medication_tier, insulin
        ORDER BY medication_tier ASC
    """
    rows = db.execute(text(sql)).fetchall()
    results = []
    for r in rows:
        tot = r[2]
        r30 = r[3]
        pct = round((r30 / tot) * 100.0, 2) if tot > 0 else 0.0
        results.append(MedicationImpactMetric(
            medication_tier=r[0],
            insulin=r[1],
            encounter_count=tot,
            readmissions_30d=r30,
            readmission_rate_pct=pct
        ))
    return results


@router.post("/predict", response_model=PredictionResponse)
def predict_encounter_risk(request: PredictionRequest):
    """
    Run real Scikit-learn inference to predict readmission probability and risk tier.
    """
    try:
        result = predict_readmission_risk(request.dict())
        return PredictionResponse(
            readmission_probability=result["readmission_probability"],
            predicted_class=result["predicted_class"],
            risk_tier=result["risk_tier"],
            recommendation=result["recommendation"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Inference pipeline execution error: {str(e)}"
        )

