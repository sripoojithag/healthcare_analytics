"""
Healthcare Data Warehouse SQLAlchemy ORM Models
Defines DimPatient, DimDiagnosis, DimEncounterContext, and FactEncounter.
"""
from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, func, Index
)
from sqlalchemy.orm import relationship
from src.warehouse.db import Base


class DimPatient(Base):
    """Patient Demographics Dimension."""
    __tablename__ = "dim_patient"

    patient_key = Column(Integer, primary_key=True, autoincrement=True)
    patient_nbr = Column(String(50), nullable=False, unique=True, index=True)
    race = Column(String(50), default="Unknown")
    gender = Column(String(50), default="Unknown/Invalid")
    age_group = Column(String(20), default="Unknown", index=True)
    weight = Column(String(50), default="Unknown")
    created_at = Column(DateTime, server_default=func.now())

    encounters = relationship("FactEncounter", back_populates="patient")


class DimDiagnosis(Base):
    """Clinical Diagnoses Dimension (ICD-9 mapped to clinical chapters)."""
    __tablename__ = "dim_diagnosis"

    diagnosis_key = Column(Integer, primary_key=True, autoincrement=True)
    diag_code = Column(String(50), nullable=False, unique=True, index=True)
    category = Column(String(100), nullable=False, index=True)
    description = Column(String(255), default="Clinical Diagnosis Code")
    created_at = Column(DateTime, server_default=func.now())

    encounters = relationship("FactEncounter", back_populates="primary_diagnosis")


class DimEncounterContext(Base):
    """Administrative & Encounter Setting Dimension."""
    __tablename__ = "dim_encounter_context"

    context_key = Column(Integer, primary_key=True, autoincrement=True)
    admission_type_id = Column(Integer, default=0)
    discharge_disposition_id = Column(Integer, default=0)
    admission_source_id = Column(Integer, default=0)
    payer_code = Column(String(50), default="Unknown")
    medical_specialty = Column(String(100), default="Unknown", index=True)
    created_at = Column(DateTime, server_default=func.now())

    encounters = relationship("FactEncounter", back_populates="context")


class FactEncounter(Base):
    """Central Inpatient Encounter Fact Table."""
    __tablename__ = "fact_encounter"

    encounter_key = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(String(50), nullable=False, unique=True, index=True)
    patient_key = Column(Integer, ForeignKey("dim_patient.patient_key"), nullable=False, index=True)
    primary_diag_key = Column(Integer, ForeignKey("dim_diagnosis.diagnosis_key"), nullable=True, index=True)
    context_key = Column(Integer, ForeignKey("dim_encounter_context.context_key"), nullable=True, index=True)

    # Utilization measures
    time_in_hospital = Column(Integer, default=1, index=True)
    num_lab_procedures = Column(Integer, default=0)
    num_procedures = Column(Integer, default=0)
    num_medications = Column(Integer, default=0)
    number_outpatient = Column(Integer, default=0)
    number_emergency = Column(Integer, default=0)
    number_inpatient = Column(Integer, default=0)
    number_diagnoses = Column(Integer, default=0)

    # Glycemic indicators
    max_glu_serum = Column(String(20), default="None")
    a1c_result = Column(String(20), default="None")

    # Pharmacotherapy
    metformin = Column(String(20), default="No")
    insulin = Column(String(20), default="No")
    change = Column(String(10), default="No")
    diabetes_med = Column(String(10), default="No")

    # Readmission outcomes
    readmitted = Column(String(20), default="NO")
    readmitted_binary = Column(Integer, default=0, index=True)
    readmitted_30d = Column(Integer, default=0, index=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    patient = relationship("DimPatient", back_populates="encounters")
    primary_diagnosis = relationship("DimDiagnosis", back_populates="encounters")
    context = relationship("DimEncounterContext", back_populates="encounters")


# Composite indexes
Index("idx_fact_readmit_metrics", FactEncounter.readmitted_30d, FactEncounter.time_in_hospital)
Index("idx_fact_patient_stay", FactEncounter.patient_key, FactEncounter.time_in_hospital)


class User(Base):
    """User accounts with secure hashed credentials and roles."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="viewer", index=True)  # "admin", "analyst", "viewer"
    status = Column(String(20), nullable=False, default="active", index=True)  # "active", "inactive"
    created_at = Column(DateTime, server_default=func.now())
    last_login_at = Column(DateTime, nullable=True)


class ActiveDataset(Base):
    """Tracks active dataset metadata, source, and validity state."""
    __tablename__ = "active_dataset"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False, default="UCI Diabetes 130-US Hospitals (1999–2008)")
    source = Column(String(150), nullable=False, default="UCI Machine Learning Repository")
    record_count = Column(Integer, nullable=False, default=0)
    date_range = Column(String(100), nullable=False, default="1999–2008 Inpatient Admissions")
    last_ingested_at = Column(DateTime, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)  # 1 = active, 0 = deleted
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class IngestionJob(Base):
    """Audit log of dataset ingestion runs with mode and record counts."""
    __tablename__ = "ingestion_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    mode = Column(String(20), nullable=False)  # "append" or "replace"
    status = Column(String(20), nullable=False)  # "SUCCESS", "FAILED", "PARTIAL"
    total_records = Column(Integer, default=0)
    inserted_records = Column(Integer, default=0)
    duplicate_records = Column(Integer, default=0)
    rejected_records = Column(Integer, default=0)
    error_summary = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class ModelArtifact(Base):
    """Registry of trained machine learning model artifacts."""
    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    version = Column(String(50), default="v1.0")
    is_active = Column(Integer, default=0)  # 1 = active, 0 = inactive
    metrics = Column(String(1000), default="{}")
    activated_by = Column(String(100), default="system")
    activated_at = Column(DateTime, server_default=func.now())


class PersistentAuditLog(Base):
    """Append-only database-backed audit log."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    user_id = Column(String(100), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    client_ip = Column(String(50), default="127.0.0.1")
    details = Column(String(2000), default="{}")
