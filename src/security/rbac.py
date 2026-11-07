"""
Role-Based Access Control (RBAC) & Security Dependencies
Enforces Admin, Analyst, and Viewer authorization tiers with audit integration.
"""
from enum import Enum
from typing import Any, List, Optional, Union
from fastapi import Header, HTTPException, Depends, Request
from pydantic import BaseModel

from src.security.audit import audit_store


class Role(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class AuthenticatedUser(BaseModel):
    user_id: str
    email: str = "user@healthcare.local"
    name: str = "Authenticated User"
    role: Role
    status: str = "active"


def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None)
) -> AuthenticatedUser:
    """
    Authenticate user via Authorization header (Signed Bearer token) or legacy development headers.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    # 1. Check Bearer token (Production Signed Tokens)
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()
            # Decode signed token
            from src.security.auth import decode_access_token
            payload = decode_access_token(token)
            if payload:
                role_val = payload.get("role", "viewer").lower()
                return AuthenticatedUser(
                    user_id=str(payload.get("sub", "user")),
                    email=payload.get("email", "user@healthcare.local"),
                    name=payload.get("name", payload.get("email", "Authenticated User")),
                    role=Role(role_val),
                    status="active"
                )
            
            # Development fallback tokens
            if "admin" in token.lower():
                return AuthenticatedUser(user_id="admin_service", email="admin@healthcare.local", name="Admin Service", role=Role.ADMIN)
            elif "analyst" in token.lower():
                return AuthenticatedUser(user_id="analyst_service", email="analyst@healthcare.local", name="Analyst Service", role=Role.ANALYST)
            elif "viewer" in token.lower():
                return AuthenticatedUser(user_id="viewer_service", email="viewer@healthcare.local", name="Viewer Service", role=Role.VIEWER)
            else:
                audit_store.log("unknown", "none", "AUTHENTICATE", str(request.url.path), "DENIED", client_ip)
                raise HTTPException(status_code=401, detail="Invalid or expired authorization token")

    # 2. Check explicit X-User-Role header (Test / Service compatibility)
    if x_user_role:
        role_str = x_user_role.lower().strip()
        if role_str in [r.value for r in Role]:
            return AuthenticatedUser(
                user_id=f"{role_str}_user",
                email=f"{role_str}@healthcare.local",
                name=f"{role_str.title()} User",
                role=Role(role_str)
            )
        else:
            audit_store.log("unknown", "none", "AUTHENTICATE", str(request.url.path), "DENIED", client_ip)
            raise HTTPException(status_code=401, detail=f"Invalid user role: {x_user_role}")

    # 3. Default unauthenticated guest has Viewer role (Read-only access to basic stats, blocked from Admin/Analyst ops)
    return AuthenticatedUser(user_id="guest_viewer", email="guest@healthcare.local", name="Guest Viewer", role=Role.VIEWER)


def require_role(allowed_roles: Any):
    """Factory creating endpoint dependencies that verify caller role."""
    if not isinstance(allowed_roles, (list, tuple, set)):
        raw_roles = [allowed_roles]
    else:
        raw_roles = list(allowed_roles)

    # Normalize to Role enum instances
    normalized_roles: List[Role] = []
    for r in raw_roles:
        if isinstance(r, Role):
            normalized_roles.append(r)
        elif isinstance(r, str):
            normalized_roles.append(Role(r.lower().strip()))

    def role_checker(
        request: Request,
        user: AuthenticatedUser = Depends(get_current_user)
    ) -> AuthenticatedUser:
        client_ip = request.client.host if request.client else "127.0.0.1"

        if user.role not in normalized_roles:
            audit_store.log(
                user_id=user.user_id,
                role=user.role.value,
                action="AUTHORIZE",
                resource=str(request.url.path),
                status="DENIED",
                client_ip=client_ip,
                details={"required_roles": [r.value for r in normalized_roles]}
            )
            raise HTTPException(
                status_code=403,
                detail=f"Access forbidden: requires one of {[r.value for r in normalized_roles]}, user has '{user.role.value}'"
            )

        audit_store.log(
            user_id=user.user_id,
            role=user.role.value,
            action="AUTHORIZE",
            resource=str(request.url.path),
            status="SUCCESS",
            client_ip=client_ip
        )
        return user

    return role_checker
