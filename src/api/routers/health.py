"""
System Health & Warehouse Connectivity Router
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.api.config import settings
from src.api.deps import get_db_session
from src.api.schemas import HealthResponse
from src.warehouse.models import FactEncounter

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
def check_health(db: Session = Depends(get_db_session)):
    """Check API operational status and data warehouse connection."""
    db_connected = False
    encounter_count = 0
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
        encounter_count = db.query(FactEncounter).count()
    except Exception:
        db_connected = False

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        version=settings.VERSION,
        database_connected=db_connected,
        total_encounters_in_warehouse=encounter_count
    )
