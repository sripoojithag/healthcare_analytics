"""
Patient Encounters Router with HIPAA-Aligned Identifier Masking
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.deps import get_db_session
from src.api.schemas import PaginatedEncountersResponse, MaskedEncounterRecord
from src.warehouse.models import FactEncounter, DimPatient, DimDiagnosis
from src.security.rbac import require_role, Role, AuthenticatedUser

router = APIRouter(prefix="/encounters", tags=["Encounters"])


def mask_patient_nbr(nbr: str) -> str:
    """Mask natural patient ID (e.g., '8222157' -> 'PT-***2157')."""
    s = str(nbr)
    suffix = s[-4:] if len(s) >= 4 else s
    return f"PT-***{suffix}"


@router.get("", response_model=PaginatedEncountersResponse)
def list_encounters(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Page size"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    readmitted_30d: Optional[int] = Query(None, description="Filter by 30-day readmission flag: 0 or 1"),
    current_user: AuthenticatedUser = Depends(require_role([Role.ADMIN, Role.ANALYST])),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve paginated clinical encounters with de-identified/masked patient numbers.
    Does not expose sensitive raw patient identifiers to analytics callers.
    """
    query = (
        db.query(FactEncounter, DimPatient, DimDiagnosis)
        .join(DimPatient, FactEncounter.patient_key == DimPatient.patient_key)
        .outerjoin(DimDiagnosis, FactEncounter.primary_diag_key == DimDiagnosis.diagnosis_key)
    )

    if gender:
        query = query.filter(DimPatient.gender == gender)
    if readmitted_30d is not None:
        query = query.filter(FactEncounter.readmitted_30d == readmitted_30d)

    total_records = query.count()
    offset = (page - 1) * page_size
    records = query.order_by(FactEncounter.encounter_key.desc()).offset(offset).limit(page_size).all()

    items = []
    for fact, patient, diag in records:
        items.append(
            MaskedEncounterRecord(
                encounter_id=fact.encounter_id,
                masked_patient_nbr=mask_patient_nbr(patient.patient_nbr),
                gender=patient.gender,
                age_group=patient.age_group,
                diagnosis_category=diag.category if diag else "Unknown",
                time_in_hospital=fact.time_in_hospital,
                num_lab_procedures=fact.num_lab_procedures,
                num_medications=fact.num_medications,
                insulin=fact.insulin,
                readmitted=fact.readmitted,
                readmitted_30d=fact.readmitted_30d
            )
        )

    return PaginatedEncountersResponse(
        total_records=total_records,
        page=page,
        page_size=page_size,
        encounters=items
    )
