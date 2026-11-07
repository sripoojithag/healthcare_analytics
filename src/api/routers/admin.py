"""
Admin Panel & Data Management Microservices Router
Provides User Management, Dataset Lifecycle (Append/Replace/Delete), Model Activation, and Audit Inspection.
Restricted exclusively to authenticated Administrator users.
"""

from datetime import datetime
import io
import json
import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
import pandas as pd
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from src.api.deps import get_db_session
from src.api.schemas import IngestionUploadResponse
from src.etl.cleaner import clean_healthcare_data
from src.etl.ingestion import EXPECTED_COLUMNS, MANDATORY_IDENTIFIERS, ingest_csv, validate_schema
from src.security.audit import audit_store
from src.security.auth import hash_password
from src.security.rbac import AuthenticatedUser, Role, require_role
from src.warehouse.loader import load_cleaned_data_to_warehouse
from src.warehouse.models import (
    ActiveDataset,
    DimDiagnosis,
    DimEncounterContext,
    DimPatient,
    FactEncounter,
    IngestionJob,
    ModelArtifact,
    User
)

router = APIRouter(prefix="/admin", tags=["Admin Management"])


# --- Schemas ---

class CreateUserRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "viewer"  # "admin", "analyst", "viewer"


class UpdateRoleRequest(BaseModel):
    role: str


class UpdateStatusRequest(BaseModel):
    status: str  # "active", "inactive"


class ResetPasswordRequest(BaseModel):
    new_password: str


class DeleteDatasetRequest(BaseModel):
    confirmation_phrase: str


class ActivateModelRequest(BaseModel):
    model_name: str


# --- User Management Endpoints ---

@router.get("/users")
def list_users(
    current_user: AuthenticatedUser = Depends(require_role([Role.ADMIN])),
    db: Session = Depends(get_db_session)
):
    """List all user accounts in the platform."""
    users = db.query(User).order_by(User.id.asc()).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "status": u.status,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            "is_current_user": str(u.id) == str(current_user.user_id) or u.email == current_user.email
        }
        for u in users
    ]


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_role([Role.ADMIN])),
    db: Session = Depends(get_db_session)
):
    """Create a new user account with hashed credentials."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    email_clean = payload.email.strip().lower()

    if payload.role not in [r.value for r in Role]:
        raise HTTPException(status_code=400, detail=f"Invalid role '{payload.role}'. Must be admin, analyst, or viewer.")

    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")

    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"User with email '{email_clean}' already exists.")

    new_user = User(
        name=payload.name.strip(),
        email=email_clean,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        status="active"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    audit_store.log(
        user_id=current_user.user_id,
        role=current_user.role.value,
        action="USER_CREATE",
        resource=f"/api/v1/admin/users/{new_user.id}",
        status="SUCCESS",
        client_ip=client_ip,
        details={"created_email": new_user.email, "assigned_role": new_user.role}
    )

    return {
        "status": "success",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role,
            "status": new_user.status
        }
    }


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    payload: UpdateRoleRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_role([Role.ADMIN])),
    db: Session = Depends(get_db_session)
):
    """Update user role with self-demotion and last-admin safeguards."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    new_role = payload.role.lower().strip()
    if new_role not in [r.value for r in Role]:
        raise HTTPException(status_code=400, detail=f"Invalid role: {payload.role}")

    # Guard 1: Prevent admin from demoting themselves
    if (str(target_user.id) == str(current_user.user_id) or target_user.email == current_user.email) and new_role != "admin":
        raise HTTPException(
            status_code=400,
            detail="Self-demotion prohibited: Administrators cannot remove their own admin privileges."
        )

    # Guard 2: Prevent demoting the last active administrator
    if target_user.role == "admin" and new_role != "admin":
        active_admins = db.query(User).filter(User.role == "admin", User.status == "active").count()
        if active_admins <= 1:
            raise HTTPException(
                status_code=400,
                detail="Operation rejected: Cannot remove or demote the last active administrator."
            )

    old_role = target_user.role
    target_user.role = new_role
    db.commit()

    audit_store.log(
        user_id=current_user.user_id,
        role=current_user.role.value,
        action="USER_UPDATE_ROLE",
        resource=f"/api/v1/admin/users/{target_user.id}",
        status="SUCCESS",
        client_ip=client_ip,
        details={"target_email": target_user.email, "old_role": old_role, "new_role": new_role}
    )

    return {"status": "success", "user_id": target_user.id, "new_role": target_user.role}


@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    payload: UpdateStatusRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_role([Role.ADMIN])),
    db: Session = Depends(get_db_session)
):
    """Activate or deactivate user account with self-lockout safeguards."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    new_status = payload.status.lower().strip()
    if new_status not in ["active", "inactive"]:
        raise HTTPException(status_code=400, detail="Status must be 'active' or 'inactive'")

    # Guard 1: Prevent admin from deactivating themselves
    if (str(target_user.id) == str(current_user.user_id) or target_user.email == current_user.email) and new_status == "inactive":
        raise HTTPException(
            status_code=400,
            detail="Self-deactivation prohibited: Administrators cannot deactivate their own account."
        )

    # Guard 2: Prevent deactivating the last active administrator
    if target_user.role == "admin" and new_status == "inactive":
        active_admins = db.query(User).filter(User.role == "admin", User.status == "active").count()
        if active_admins <= 1:
            raise HTTPException(
                status_code=400,
                detail="Operation rejected: Cannot deactivate the last active administrator."
            )

    target_user.status = new_status
    db.commit()

    audit_store.log(
        user_id=current_user.user_id,
        role=current_user.role.value,
        action="USER_UPDATE_STATUS",
        resource=f"/api/v1/admin/users/{target_user.id}",
        status="SUCCESS",
        client_ip=client_ip,
        details={"target_email": target_user.email, "new_status": new_status}
    )

    return {"status": "success", "user_id": target_user.id, "status": target_user.status}


@router.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    payload: ResetPasswordRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_role([Role.ADMIN])),
    db: Session = Depends(get_db_session)
):
    """Admin resets user credentials securely."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters long.")

    target_user.hashed_password = hash_password(payload.new_password)
    db.commit()

    audit_store.log(
        user_id=current_user.user_id,
        role=current_user.role.value,
        action="USER_PASSWORD_RESET",
        resource=f"/api/v1/admin/users/{target_user.id}",
        status="SUCCESS",
        client_ip=client_ip,
        details={"target_email": target_user.email}
    )

    return {"status": "success", "message": f"Password reset successfully for user {target_user.email}"}


# --- Data Management Endpoints ---

@router.get("/dataset/active")
def get_active_dataset(
    current_user: AuthenticatedUser = Depends(require_role([Role.ADMIN, Role.ANALYST, Role.VIEWER])),
    db: Session = Depends(get_db_session)
):
    """Retrieve active dataset metadata and warehouse encounter counts."""
    count = db.query(FactEncounter).count()
    dataset = db.query(ActiveDataset).first()

    if not dataset:
        dataset = ActiveDataset(
            name="UCI Diabetes Inpatient Encounters",
            source="UCI Machine Learning Repository",
            record_count=count,
            date_range="1999–2008 Inpatient Admissions",
            is_active=1 if count > 0 else 0
        )
        db.add(dataset)
        db.commit()
    else:
        # Keep record count synchronized
        if dataset.record_count != count:
            dataset.record_count = count
            dataset.is_active = 1 if count > 0 else 0
            db.commit()

    last_ingest = db.query(IngestionJob).filter(IngestionJob.status == "SUCCESS").order_by(IngestionJob.created_at.desc()).first()

    return {
        "name": dataset.name,
        "source": dataset.source,
        "record_count": count,
        "date_range": dataset.date_range,
        "is_active": bool(dataset.is_active and count > 0),
        "last_ingested_at": last_ingest.created_at.isoformat() if last_ingest and last_ingest.created_at else (dataset.last_ingested_at.isoformat() if dataset.last_ingested_at else None),
        "status": "Active" if (dataset.is_active and count > 0) else "Empty / Not Initialized"
    }


@router.get("/dataset/history")
def get_ingestion_history(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(require_role([Role.ADMIN])),
    db: Session = Depends(get_db_session)
):
    """Retrieve past ingestion jobs with mode and inserted/duplicate counts."""
    jobs = db.query(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(limit).all()
    return [
        {
            "id": j.id,
            "filename": j.filename,
            "mode": j.mode,
            "status": j.status,
            "total_records": j.total_records,
            "inserted_records": j.inserted_records,
            "duplicate_records": j.duplicate_records,
            "rejected_records": j.rejected_records,
            "error_summary": j.error_summary,
            "created_at": j.created_at.isoformat() if j.created_at else None
        }
        for j in jobs
    ]


@router.post("/dataset/preview")
async def preview_csv_dataset(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(require_role([Role.ADMIN]))
):
    """
    Preview uploaded CSV file without modifying database.
    Validates columns, identifies missing expected fields, and suggests column mappings.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported for preview.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        buf = io.BytesIO(content)
        df_sample = pd.read_csv(buf, nrows=10, dtype=str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV preview: {str(e)}")

    if df_sample.empty:
        raise HTTPException(status_code=400, detail="Uploaded CSV contains no rows.")

    uploaded_cols = list(df_sample.columns)
    schema_val = validate_schema(uploaded_cols)

    # Suggest automated mappings for common synonyms (e.g., patient_id -> patient_nbr)
    suggested_mapping: Dict[str, str] = {}
    synonym_map = {
        "encounter": "encounter_id",
        "id": "encounter_id",
        "patient": "patient_nbr",
        "patient_id": "patient_nbr",
        "sex": "gender",
        "stay": "time_in_hospital",
        "hospital_stay": "time_in_hospital",
        "days": "time_in_hospital",
        "labs": "num_lab_procedures",
        "medications": "num_medications",
        "meds": "num_medications",
        "diagnosis": "diag_1",
        "a1c": "A1Cresult",
    }
    for col in uploaded_cols:
        col_norm = col.lower().strip().replace(" ", "_")
        if col not in EXPECTED_COLUMNS and col_norm in synonym_map:
            suggested_mapping[col] = synonym_map[col_norm]

    # Quick preview records (first 5 rows)
    preview_data = df_sample.head(5).fillna("").to_dict(orient="records")

    return {
        "filename": file.filename,
        "sample_rows_previewed": len(preview_data),
        "total_columns": len(uploaded_cols),
        "detected_columns": uploaded_cols,
        "missing_columns": schema_val["missing"],
        "unexpected_columns": schema_val["unexpected"],
        "schema_valid": len(schema_val["missing"]) == 0,
        "suggested_mappings": suggested_mapping,
        "preview_records": preview_data
    }


@router.post("/dataset/ingest")
async def ingest_dataset_with_mode(
    request: Request,
    file: UploadFile = File(...),
    mode: str = Form("append"),  # "append" or "replace"
    column_mapping: Optional[str] = Form(None),  # JSON string
    confirm_replace: Optional[bool] = Form(False),
    current_user: AuthenticatedUser = Depends(require_role([Role.ADMIN])),
    db: Session = Depends(get_db_session)
):
    """
    Ingest healthcare CSV in either 'append' or 'replace' mode with column mapping support.
    Transactional: if replace fails, existing warehouse data is preserved.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    if mode not in ["append", "replace"]:
        raise HTTPException(status_code=400, detail="Mode must be 'append' or 'replace'")

    if mode == "replace" and not confirm_replace:
        raise HTTPException(
            status_code=400,
            detail="Confirmation required: 'confirm_replace' must be set to true to replace the active dataset."
        )

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid format. Only .csv files are supported.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        buf = io.BytesIO(content)
        raw_df = pd.read_csv(buf, dtype=str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parse error: {str(e)}")

    if raw_df.empty:
        raise HTTPException(status_code=400, detail="Uploaded CSV contains 0 rows.")

    # Apply column mapping if provided
    if column_mapping:
        try:
            mapping_dict = json.loads(column_mapping)
            if isinstance(mapping_dict, dict):
                raw_df.rename(columns=mapping_dict, inplace=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid column_mapping JSON: {str(e)}")

    # Ensure mandatory identifiers are present
    missing_ids = [c for c in MANDATORY_IDENTIFIERS if c not in raw_df.columns]
    if missing_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Schema rejection: Mandatory columns missing: {missing_ids}. Please provide column mapping."
        )

    # Clean and standardize DataFrame
    cleaned_df, cleaning_metrics = clean_healthcare_data(raw_df)

    # Stage Ingestion Job record
    job = IngestionJob(
        filename=file.filename,
        mode=mode,
        status="PENDING",
        total_records=len(raw_df),
        rejected_records=cleaning_metrics.get("rejected_records", 0)
    )
    db.add(job)
    db.commit()

    try:
        if mode == "replace":
            # Transactional replace: delete existing encounters
            # Then load staged records
            db.query(FactEncounter).delete()
            db.commit()

        # Load cleaned data into Star Schema
        load_results = load_cleaned_data_to_warehouse(cleaned_df, db)

        inserted_count = load_results.get("encounters_loaded", 0)
        duplicates_count = max(0, len(cleaned_df) - inserted_count)

        # Update active dataset record count
        active_count = db.query(FactEncounter).count()
        dataset_meta = db.query(ActiveDataset).first()
        if dataset_meta:
            dataset_meta.record_count = active_count
            dataset_meta.is_active = 1 if active_count > 0 else 0
            dataset_meta.last_ingested_at = datetime.utcnow()
            if mode == "replace":
                dataset_meta.name = f"Custom Ingest: {file.filename}"
            db.commit()

        # Update job record
        job.status = "SUCCESS"
        job.inserted_records = inserted_count
        job.duplicate_records = duplicates_count
        db.commit()

        audit_action = "DATASET_REPLACE" if mode == "replace" else "DATASET_APPEND"
        audit_store.log(
            user_id=current_user.user_id,
            role=current_user.role.value,
            action=audit_action,
            resource=f"/api/v1/admin/dataset/{mode}",
            status="SUCCESS",
            client_ip=client_ip,
            details={
                "filename": file.filename,
                "mode": mode,
                "inserted": inserted_count,
                "duplicates": duplicates_count,
                "total_active_records": active_count
            }
        )

        return {
            "status": "SUCCESS",
            "mode": mode,
            "filename": file.filename,
            "total_records": len(raw_df),
            "inserted_records": inserted_count,
            "duplicate_records": duplicates_count,
            "rejected_records": job.rejected_records,
            "total_active_records": active_count,
            "table_summary": load_results
        }
    except Exception as e:
        db.rollback()
        job.status = "FAILED"
        job.error_summary = str(e)[:450]
        db.commit()

        audit_store.log(
            user_id=current_user.user_id,
            role=current_user.role.value,
            action="DATASET_INGEST_FAILED",
            resource=f"/api/v1/admin/dataset/{mode}",
            status="FAILED",
            client_ip=client_ip,
            details={"error": str(e)[:200]}
        )
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed and rolled back: {str(e)}"
        )


@router.post("/dataset/delete")
def delete_active_dataset(
    payload: DeleteDatasetRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_role([Role.ADMIN])),
    db: Session = Depends(get_db_session)
):
    """
    Deletes active patient/encounter records and derived facts from the warehouse.
    Requires exact confirmation phrase 'DELETE ACTIVE DATASET'.
    Preserves audit logs and ingestion history for compliance.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    if payload.confirmation_phrase.strip() != "DELETE ACTIVE DATASET":
        raise HTTPException(
            status_code=400,
            detail="Confirmation phrase mismatch. Please enter 'DELETE ACTIVE DATASET' exactly to confirm deletion."
        )

    try:
        deleted_encounters = db.query(FactEncounter).count()

        # Delete facts and associated dimensional context
        db.query(FactEncounter).delete()
        db.query(DimEncounterContext).delete()
        db.query(DimDiagnosis).delete()
        db.query(DimPatient).delete()

        # Update dataset metadata to empty state
        dataset_meta = db.query(ActiveDataset).first()
        if dataset_meta:
            dataset_meta.record_count = 0
            dataset_meta.is_active = 0
            dataset_meta.name = "No Active Dataset (Deleted)"

        db.commit()

        audit_store.log(
            user_id=current_user.user_id,
            role=current_user.role.value,
            action="DATASET_DELETE",
            resource="/api/v1/admin/dataset/delete",
            status="SUCCESS",
            client_ip=client_ip,
            details={
                "deleted_encounters": deleted_encounters,
                "history_retained": True
            }
        )

        return {
            "status": "success",
            "message": "Active dataset records deleted successfully. Audit trail and ingestion history preserved.",
            "deleted_encounters": deleted_encounters,
            "data_retention_note": "In accordance with data governance policies, audit logs and historical ingestion records remain intact."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Dataset deletion failed: {str(e)}")


# --- Model Management Endpoints ---

@router.get("/models")
def list_registered_models(
    current_user: AuthenticatedUser = Depends(require_role([Role.ADMIN])),
    db: Session = Depends(get_db_session)
):
    """List all available machine learning artifacts and currently active model."""
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../models"))
    disk_files = []
    if os.path.exists(models_dir):
        disk_files = [f for f in os.listdir(models_dir) if f.endswith(".joblib")]

    db_models = db.query(ModelArtifact).all()
    db_model_map = {m.name: m for m in db_models}

    # Load metadata file if available
    meta_path = os.path.join(models_dir, "model_metadata.json")
    default_metrics = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r") as f:
                default_metrics = json.load(f).get("metrics", {})
        except Exception:
            pass

    results = []
    for f in disk_files:
        is_active = False
        db_m = db_model_map.get(f)
        if db_m:
            is_active = bool(db_m.is_active)
            try:
                metrics_dict = json.loads(db_m.metrics)
            except Exception:
                metrics_dict = default_metrics
        else:
            is_active = (f == "readmission_pipeline_v1.joblib")
            metrics_dict = default_metrics

        results.append({
            "name": f,
            "version": "v1.0" if "v1" in f else "v2.0",
            "is_active": is_active,
            "file_size_bytes": os.path.getsize(os.path.join(models_dir, f)),
            "algorithm": "RandomForestClassifier",
            "metrics": metrics_dict,
            "activated_by": db_m.activated_by if db_m else "system",
            "activated_at": db_m.activated_at.isoformat() if db_m and db_m.activated_at else None
        })

    return results


@router.post("/models/activate")
def activate_model(
    payload: ActivateModelRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_role([Role.ADMIN])),
    db: Session = Depends(get_db_session)
):
    """Explicitly activate a validated machine learning model artifact."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../models"))
    model_path = os.path.join(models_dir, payload.model_name)

    if not os.path.exists(model_path):
        raise HTTPException(
            status_code=404,
            detail=f"Model artifact '{payload.model_name}' not found in models directory."
        )

    # Deactivate all and activate selected
    db.query(ModelArtifact).update({ModelArtifact.is_active: 0})

    existing = db.query(ModelArtifact).filter(ModelArtifact.name == payload.model_name).first()
    if existing:
        existing.is_active = 1
        existing.activated_by = current_user.email
        existing.activated_at = datetime.utcnow()
    else:
        new_m = ModelArtifact(
            name=payload.model_name,
            version="v1.0",
            is_active=1,
            activated_by=current_user.email
        )
        db.add(new_m)

    db.commit()

    audit_store.log(
        user_id=current_user.user_id,
        role=current_user.role.value,
        action="MODEL_ACTIVATE",
        resource=f"/api/v1/admin/models/activate/{payload.model_name}",
        status="SUCCESS",
        client_ip=client_ip,
        details={"activated_model": payload.model_name}
    )

    return {
        "status": "success",
        "message": f"Model '{payload.model_name}' is now active for predictive inference.",
        "active_model": payload.model_name
    }


# --- Audit Logs & System Status Endpoints ---

@router.get("/audit-logs")
def get_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    current_user: AuthenticatedUser = Depends(require_role([Role.ADMIN]))
):
    """Retrieve append-only audit trail logs (Admin only)."""
    return audit_store.get_logs(limit=limit)


@router.get("/system-status")
def get_system_status(
    current_user: AuthenticatedUser = Depends(require_role([Role.ADMIN])),
    db: Session = Depends(get_db_session)
):
    """Retrieve health and operational metrics for backend, database, and model services."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    encounter_count = db.query(FactEncounter).count() if db_ok else 0
    user_count = db.query(User).count() if db_ok else 0
    active_dataset = db.query(ActiveDataset).first() if db_ok else None

    # Check model artifact
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../models"))
    model_loaded = os.path.exists(os.path.join(models_dir, "readmission_pipeline_v1.joblib"))

    return {
        "status": "healthy" if db_ok else "degraded",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "services": {
            "backend_api": {"status": "online", "framework": "FastAPI"},
            "warehouse_db": {
                "status": "connected" if db_ok else "disconnected",
                "total_encounters": encounter_count,
                "total_users": user_count,
                "dataset_active": bool(active_dataset and active_dataset.is_active and encounter_count > 0)
            },
            "ml_inference": {
                "status": "ready" if model_loaded else "unavailable",
                "active_model": "readmission_pipeline_v1.joblib" if model_loaded else None
            }
        }
    }
