"""
Pydantic Schemas for API Requests and Responses
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    database_connected: bool
    total_encounters_in_warehouse: int


class KPIResponse(BaseModel):
    total_encounters: int
    unique_patients: int
    readmitted_30d_count: int
    readmitted_30d_rate_pct: float
    total_readmissions_count: int
    total_readmission_rate_pct: float
    avg_length_of_stay_days: float
    avg_lab_procedures: float
    avg_medications_per_encounter: float


class AgeCohortMetric(BaseModel):
    age_group: str
    total_encounters: int
    unique_patients: int
    readmitted_30d: int
    readmission_30d_pct: float
    avg_hospital_stay: float
    avg_medications: float


class StayCorrelationMetric(BaseModel):
    stay_days: int
    total_patients: int
    readmitted_30d: int
    readmission_30d_rate_pct: float
    avg_labs: float
    avg_meds: float


class DiagnosisRiskMetric(BaseModel):
    diagnosis_category: str
    encounters: int
    readmissions_under_30: int
    readmission_rate_pct: float
    avg_length_of_stay: float
    risk_rank: int


class MedicationImpactMetric(BaseModel):
    medication_tier: str
    insulin: str
    encounter_count: int
    readmissions_30d: int
    readmission_rate_pct: float


class MaskedEncounterRecord(BaseModel):
    encounter_id: str
    masked_patient_nbr: str
    gender: str
    age_group: str
    diagnosis_category: Optional[str]
    time_in_hospital: int
    num_lab_procedures: int
    num_medications: int
    insulin: str
    readmitted: str
    readmitted_30d: int


class PaginatedEncountersResponse(BaseModel):
    total_records: int
    page: int
    page_size: int
    encounters: List[MaskedEncounterRecord]


class DataQualitySummaryResponse(BaseModel):
    dataset_name: str
    total_records: int
    total_columns: int
    duplicate_rows: int
    overall_completeness_pct: float
    quality_grade: str
    validity_checks: Dict[str, Any]


class IngestionUploadResponse(BaseModel):
    status: str
    filename: str
    total_records: int
    valid_records: int
    rejected_records: int
    errors: List[str]
    missing_columns: List[str]


class PredictionRequest(BaseModel):
    time_in_hospital: int = Field(default=3, ge=1, le=14)
    num_lab_procedures: int = Field(default=40, ge=1, le=150)
    num_procedures: int = Field(default=1, ge=0, le=10)
    num_medications: int = Field(default=12, ge=1, le=80)
    number_outpatient: int = Field(default=0, ge=0)
    number_emergency: int = Field(default=0, ge=0)
    number_inpatient: int = Field(default=0, ge=0)
    number_diagnoses: int = Field(default=7, ge=1, le=20)
    age: str = "[60-70)"
    gender: str = "Female"
    race: str = "Caucasian"
    insulin: str = "Steady"
    diabetesMed: str = "Yes"


class PredictionResponse(BaseModel):
    readmission_probability: float
    predicted_class: int
    risk_tier: str
    recommendation: str


# --- Phase 8: DSA Schemas ---

class TriageEnqueueRequest(BaseModel):
    encounter_id: str
    patient_id: str
    risk_score: float = Field(ge=0.0, le=1.0)
    time_in_hospital: int = Field(default=0, ge=0)
    num_medications: int = Field(default=0, ge=0)
    primary_diagnosis: str = "Unknown"
    notes: Optional[str] = None


class TriageItemResponse(BaseModel):
    encounter_id: str
    patient_id: str
    risk_score: float
    time_in_hospital: int
    num_medications: int
    primary_diagnosis: str
    metadata: Dict[str, Any] = {}


class TriageQueueStatusResponse(BaseModel):
    total_queued: int
    is_empty: bool
    top_patient: Optional[TriageItemResponse] = None
    queue_preview: List[TriageItemResponse] = []


class GraphTraverseRequest(BaseModel):
    start_node: str = "Diabetes"
    algorithm: str = Field(default="bfs", pattern="^(bfs|dfs)$")
    visit_all_components: bool = False


class GraphTraverseResponse(BaseModel):
    start_node: str
    algorithm: str
    traversal_path: List[str]
    total_visited: int
    time_complexity: str = "O(V + E)"
    space_complexity: str = "O(V)"


class GraphShortestPathRequest(BaseModel):
    start_node: str = "Diabetes"
    target_node: str = "Respiratory"


class GraphShortestPathResponse(BaseModel):
    start_node: str
    target_node: str
    path: Optional[List[str]]
    hops: Optional[int]
    path_found: bool


