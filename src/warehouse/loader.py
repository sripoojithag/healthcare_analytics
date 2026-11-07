"""
Healthcare Data Warehouse ETL Loader
Loads cleaned DataFrame records into the Star Schema tables with key resolution and deduplication.
"""
from typing import Dict, Any, Optional
import pandas as pd
from sqlalchemy.orm import Session
from src.warehouse.models import DimPatient, DimDiagnosis, DimEncounterContext, FactEncounter


def categorize_icd9(code: Optional[str]) -> str:
    """Map ICD-9 code string to high-level clinical category."""
    if not code or str(code).strip() in ["Unknown", "?", "nan", "None"]:
        return "Unknown"

    code_str = str(code).strip()
    if code_str.startswith("250"):
        return "Diabetes"
    if code_str.startswith("V") or code_str.startswith("E"):
        return "External/Supplementary"

    try:
        val = float(code_str)
        if 390 <= val <= 459 or val == 785:
            return "Circulatory"
        elif 460 <= val <= 519 or val == 786:
            return "Respiratory"
        elif 520 <= val <= 579 or val == 787:
            return "Digestive"
        elif 580 <= val <= 629 or val == 788:
            return "Genitourinary"
        elif 140 <= val <= 239:
            return "Neoplasms"
        elif 710 <= val <= 739:
            return "Musculoskeletal"
        elif 800 <= val <= 999:
            return "Injury & Poisoning"
        else:
            return "Other Medical Conditions"
    except ValueError:
        return "Other Medical Conditions"


def load_cleaned_data_to_warehouse(
    df: pd.DataFrame,
    session: Session,
    batch_size: int = 1000
) -> Dict[str, int]:
    """
    ETL Loader: Populate DimPatient, DimDiagnosis, DimEncounterContext, and FactEncounter.
    
    Args:
        df: Cleaned healthcare records DataFrame.
        session: Active SQLAlchemy session.
        batch_size: Commit batch size.
        
    Returns:
        Dictionary of row counts loaded per star schema table.
    """
    # 1. Cache existing dimensions to avoid duplicate inserts
    patient_cache: Dict[str, int] = {
        p.patient_nbr: p.patient_key for p in session.query(DimPatient.patient_nbr, DimPatient.patient_key).all()
    }
    diag_cache: Dict[str, int] = {
        d.diag_code: d.diagnosis_key for d in session.query(DimDiagnosis.diag_code, DimDiagnosis.diagnosis_key).all()
    }

    patients_loaded = 0
    diagnoses_loaded = 0
    contexts_loaded = 0
    encounters_loaded = 0

    # Cache existing encounters to ensure idempotence
    existing_encounters = set(
        e[0] for e in session.query(FactEncounter.encounter_id).all()
    )

    # 2. Extract and insert unique patients not in cache
    new_patients = []
    unique_patients = df[["patient_nbr", "race", "gender", "age", "weight"]].drop_duplicates(subset=["patient_nbr"])
    for _, row in unique_patients.iterrows():
        nbr = str(row["patient_nbr"])
        if nbr not in patient_cache:
            p = DimPatient(
                patient_nbr=nbr,
                race=str(row.get("race", "Unknown")),
                gender=str(row.get("gender", "Unknown/Invalid")),
                age_group=str(row.get("age", "Unknown")),
                weight=str(row.get("weight", "Unknown"))
            )
            new_patients.append(p)

    if new_patients:
        session.bulk_save_objects(new_patients)
        session.commit()
        # Refresh cache
        patient_cache = {
            p.patient_nbr: p.patient_key for p in session.query(DimPatient.patient_nbr, DimPatient.patient_key).all()
        }
        patients_loaded = len(new_patients)

    # 3. Extract and insert unique diagnoses not in cache
    new_diags = []
    all_codes = set()
    for col in ["diag_1", "diag_2", "diag_3"]:
        if col in df.columns:
            all_codes.update(df[col].dropna().unique())

    for code in all_codes:
        code_str = str(code).strip()
        if code_str and code_str not in diag_cache:
            d = DimDiagnosis(
                diag_code=code_str,
                category=categorize_icd9(code_str),
                description=f"ICD-9 Diagnosis: {code_str}"
            )
            new_diags.append(d)

    if new_diags:
        session.bulk_save_objects(new_diags)
        session.commit()
        diag_cache = {
            d.diag_code: d.diagnosis_key for d in session.query(DimDiagnosis.diag_code, DimDiagnosis.diagnosis_key).all()
        }
        diagnoses_loaded = len(new_diags)

    # 4. Process Context and Fact records
    fact_batch = []
    for _, row in df.iterrows():
        enc_id = str(row["encounter_id"])
        if enc_id in existing_encounters:
            continue

        p_nbr = str(row["patient_nbr"])
        p_key = patient_cache.get(p_nbr)
        if not p_key:
            continue

        primary_code = str(row.get("diag_1", "Unknown")).strip()
        d_key = diag_cache.get(primary_code)

        # Create encounter context
        context = DimEncounterContext(
            admission_type_id=int(row.get("admission_type_id", 0)),
            discharge_disposition_id=int(row.get("discharge_disposition_id", 0)),
            admission_source_id=int(row.get("admission_source_id", 0)),
            payer_code=str(row.get("payer_code", "Unknown")),
            medical_specialty=str(row.get("medical_specialty", "Unknown"))
        )
        session.add(context)
        session.flush()  # get context.context_key
        contexts_loaded += 1

        fact = FactEncounter(
            encounter_id=enc_id,
            patient_key=p_key,
            primary_diag_key=d_key,
            context_key=context.context_key,
            time_in_hospital=int(row.get("time_in_hospital", 1)),
            num_lab_procedures=int(row.get("num_lab_procedures", 0)),
            num_procedures=int(row.get("num_procedures", 0)),
            num_medications=int(row.get("num_medications", 0)),
            number_outpatient=int(row.get("number_outpatient", 0)),
            number_emergency=int(row.get("number_emergency", 0)),
            number_inpatient=int(row.get("number_inpatient", 0)),
            number_diagnoses=int(row.get("number_diagnoses", 0)),
            max_glu_serum=str(row.get("max_glu_serum", "None")),
            a1c_result=str(row.get("A1Cresult", "None")),
            metformin=str(row.get("metformin", "No")),
            insulin=str(row.get("insulin", "No")),
            change=str(row.get("change", "No")),
            diabetes_med=str(row.get("diabetesMed", "No")),
            readmitted=str(row.get("readmitted", "NO")),
            readmitted_binary=int(row.get("readmitted_binary", 0)),
            readmitted_30d=int(row.get("readmitted_30d", 0))
        )
        fact_batch.append(fact)
        existing_encounters.add(enc_id)

        if len(fact_batch) >= batch_size:
            session.bulk_save_objects(fact_batch)
            session.commit()
            encounters_loaded += len(fact_batch)
            fact_batch = []

    if fact_batch:
        session.bulk_save_objects(fact_batch)
        session.commit()
        encounters_loaded += len(fact_batch)

    return {
        "patients_loaded": patients_loaded,
        "diagnoses_loaded": diagnoses_loaded,
        "contexts_loaded": contexts_loaded,
        "encounters_loaded": encounters_loaded
    }
