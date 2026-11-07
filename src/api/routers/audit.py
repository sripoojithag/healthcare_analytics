"""
Audit Log Router for Security Governance (Admin Only)
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from src.security.rbac import require_role, Role, AuthenticatedUser
from src.security.audit import audit_store

router = APIRouter(prefix="/audit", tags=["Security & Audit"])


@router.get("/logs", response_model=List[Dict[str, Any]])
def get_audit_trail(
    limit: int = Query(50, ge=1, le=200),
    current_user: AuthenticatedUser = Depends(require_role([Role.ADMIN]))
):
    """
    Retrieve security audit trail. Restricted to administrators only.
    """
    return audit_store.get_logs(limit=limit)
