"""
Data Ingestion API Router
Validates incoming CSV payloads and tracks ingestion status without silent drops.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import io

from src.api.schemas import IngestionUploadResponse
from src.etl.ingestion import ingest_csv
from src.security.rbac import require_role, Role, AuthenticatedUser

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.post("/upload", response_model=IngestionUploadResponse)
async def upload_healthcare_csv(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(require_role([Role.ADMIN]))
):
    """
    Ingest healthcare CSV file, perform schema validation, and report rejected records.
    Restricted to Administrator role.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only .csv files are supported."
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    buf = io.BytesIO(content)
    result = ingest_csv(buf)

    return IngestionUploadResponse(
        status=result.status,
        filename=file.filename,
        total_records=result.total_records,
        valid_records=result.valid_records,
        rejected_records=result.rejected_records,
        errors=result.errors,
        missing_columns=result.missing_columns
    )
