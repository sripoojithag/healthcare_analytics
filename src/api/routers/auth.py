"""
Authentication API Router: Real login, logout, and user profile verification.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from src.api.deps import get_db_session
from src.security.auth import (
    create_access_token,
    decode_access_token,
    revoke_token,
    verify_password
)
from src.security.audit import audit_store
from src.security.rbac import AuthenticatedUser, Role, get_current_user
from src.warehouse.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str
    password: str


class UserProfileResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    status: str
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Authenticate user with email and password.
    Returns signed access token and user role.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    email_clean = payload.email.strip().lower()

    user = db.query(User).filter(User.email == email_clean).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        audit_store.log(
            user_id=email_clean,
            role="none",
            action="LOGIN_FAILED",
            resource="/api/v1/auth/login",
            status="DENIED",
            client_ip=client_ip,
            details={"reason": "Invalid email or password"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if user.status != "active":
        audit_store.log(
            user_id=str(user.id),
            role=user.role,
            action="LOGIN_BLOCKED",
            resource="/api/v1/auth/login",
            status="DENIED",
            client_ip=client_ip,
            details={"reason": "Account is inactive"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact an administrator."
        )

    # Update last login timestamp
    user.last_login_at = datetime.utcnow()
    db.commit()

    token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role
    )

    audit_store.log(
        user_id=str(user.id),
        role=user.role,
        action="LOGIN_SUCCESS",
        resource="/api/v1/auth/login",
        status="SUCCESS",
        client_ip=client_ip
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfileResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            status=user.status,
            created_at=user.created_at.isoformat() if user.created_at else None,
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None
        )
    )


@router.post("/logout")
def logout(
    request: Request,
    authorization: Optional[str] = Header(None),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Revoke bearer token and log out user.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split()[1]
        revoke_token(token)

    audit_store.log(
        user_id=current_user.user_id,
        role=current_user.role.value,
        action="LOGOUT",
        resource="/api/v1/auth/logout",
        status="SUCCESS",
        client_ip=client_ip
    )
    return {"status": "success", "message": "Successfully logged out"}


@router.get("/me", response_model=UserProfileResponse)
def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Return current authenticated user profile.
    """
    if current_user.user_id == "guest_viewer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in."
        )

    # Try resolving user from DB
    try:
        user_id_int = int(current_user.user_id)
        user = db.query(User).filter(User.id == user_id_int).first()
        if user:
            return UserProfileResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role,
                status=user.status,
                created_at=user.created_at.isoformat() if user.created_at else None,
                last_login_at=user.last_login_at.isoformat() if user.last_login_at else None
            )
    except (ValueError, TypeError):
        pass

    # Fallback to current_user fields
    return UserProfileResponse(
        id=0,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role.value,
        status=current_user.status
    )
