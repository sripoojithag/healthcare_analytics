"""
Unit & API Tests for Authentication, Password Hashing, and Session Tokens.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.api.deps import get_db_session
from src.warehouse.db import Base
from src.security.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    revoke_token,
    seed_default_users
)
from src.warehouse.models import User

# In-memory test engine
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
Base.metadata.create_all(bind=test_engine)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_auth_database():
    """Seed test users into test database."""
    session = TestSession()
    seed_default_users(session)
    session.close()

    def override_get_db():
        s = TestSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db_session] = override_get_db
    yield
    app.dependency_overrides.pop(get_db_session, None)


def test_password_hashing_and_verification():
    """Verify PBKDF2 password hashing produces secure salted hashes."""
    pwd = "MySecretPassword123!"
    hashed = hash_password(pwd)
    assert hashed.startswith("pbkdf2:sha256:100000$")
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(pwd, "") is False


def test_token_creation_and_decoding():
    """Verify signed access tokens encode claims and verify signatures."""
    token = create_access_token(user_id=1, email="test@example.com", role="analyst", expires_in_seconds=3600)
    assert token is not None
    assert "." in token

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "analyst"

    # Revoke token
    revoke_token(token)
    assert decode_access_token(token) is None


def test_login_success_admin():
    """Verify admin login returns valid access token and user profile."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "admin@healthcare.local",
        "password": "AdminSecure#2026!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@healthcare.local"
    assert data["user"]["role"] == "admin"
    assert data["user"]["status"] == "active"


def test_login_invalid_password():
    """Verify login with incorrect password returns 401."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "admin@healthcare.local",
        "password": "WrongPassword123"
    })
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]


def test_login_nonexistent_user():
    """Verify login with unknown email returns 401."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "ghost@healthcare.local",
        "password": "Password123!"
    })
    assert resp.status_code == 401


def test_login_deactivated_user():
    """Verify deactivated account cannot log in (403)."""
    session = TestSession()
    inactive_user = User(
        email="inactive@healthcare.local",
        name="Inactive User",
        hashed_password=hash_password("InactivePass#2026"),
        role="viewer",
        status="inactive"
    )
    session.add(inactive_user)
    session.commit()
    session.close()

    resp = client.post("/api/v1/auth/login", json={
        "email": "inactive@healthcare.local",
        "password": "InactivePass#2026"
    })
    assert resp.status_code == 403
    assert "deactivated" in resp.json()["detail"].lower()


def test_get_me_endpoint():
    """Verify /auth/me returns profile for authenticated user and rejects guests."""
    # Guest viewer (no token) -> 401
    resp_guest = client.get("/api/v1/auth/me")
    assert resp_guest.status_code == 401

    # Login to get token
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "analyst@healthcare.local",
        "password": "AnalystSecure#2026!"
    })
    token = login_resp.json()["access_token"]

    resp_auth = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp_auth.status_code == 200
    user_data = resp_auth.json()
    assert user_data["email"] == "analyst@healthcare.local"
    assert user_data["role"] == "analyst"


def test_logout_revokes_token():
    """Verify logout invalidates token."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "viewer@healthcare.local",
        "password": "ViewerSecure#2026!"
    })
    token = login_resp.json()["access_token"]

    # Verify token works
    resp1 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp1.status_code == 200

    # Logout
    logout_resp = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200

    # Subsequent request with revoked token must fail with 401
    resp2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 401
