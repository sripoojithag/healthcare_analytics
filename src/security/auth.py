"""
Authentication & Cryptographic Utilities
Implements PBKDF2-HMAC-SHA256 password hashing, signed session tokens, and default user seeding.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from src.api.config import settings
from src.warehouse.models import User, ActiveDataset, ModelArtifact, FactEncounter

# In-memory token blacklist for explicit logout / revocation
_revoked_tokens = set()


def hash_password(password: str) -> str:
    """
    Hashes password using PBKDF2-HMAC-SHA256 with a cryptographically random salt.
    Format: pbkdf2:sha256:100000$<salt_hex>$<hash_hex>
    """
    if not password:
        raise ValueError("Password cannot be empty")
    salt = secrets.token_bytes(16)
    iterations = 100000
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2:sha256:{iterations}${salt.hex()}${hash_bytes.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """
    Verifies password against stored PBKDF2 hash using constant-time comparison.
    """
    if not password or not hashed or not hashed.startswith("pbkdf2:sha256:"):
        return False
    try:
        parts = hashed.split("$")
        if len(parts) != 3:
            return False
        meta, salt_hex, target_hash_hex = parts
        iterations = int(meta.split(":")[2])
        salt = bytes.fromhex(salt_hex)
        hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(hash_bytes.hex(), target_hash_hex)
    except Exception:
        return False


def create_access_token(
    user_id: int,
    email: str,
    role: str,
    expires_in_seconds: int = 86400  # 24 hours
) -> str:
    """
    Creates a signed bearer token containing claims and an HMAC-SHA256 signature.
    """
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": int(time.time()) + expires_in_seconds,
        "jti": secrets.token_hex(8)
    }
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode('utf-8').rstrip('=')

    secret = settings.SECRET_KEY.encode('utf-8')
    signature = hmac.new(secret, payload_b64.encode('utf-8'), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')

    return f"{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validates token signature and expiration, checking against revoked token cache.
    """
    if not token or token in _revoked_tokens:
        return None

    parts = token.split('.')
    if len(parts) != 2:
        return None

    payload_b64, sig_b64 = parts
    try:
        # Verify HMAC signature
        secret = settings.SECRET_KEY.encode('utf-8')
        expected_sig = hmac.new(secret, payload_b64.encode('utf-8'), hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode('utf-8').rstrip('=')

        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None

        # Decode JSON payload with padding correction
        rem = len(payload_b64) % 4
        padded_b64 = payload_b64 + ('=' * (4 - rem) if rem else '')
        payload_data = json.loads(base64.urlsafe_b64decode(padded_b64).decode('utf-8'))

        # Check expiration
        if payload_data.get("exp", 0) < time.time():
            return None

        return payload_data
    except Exception:
        return None


def revoke_token(token: str) -> None:
    """Marks a token as revoked on logout."""
    if token:
        _revoked_tokens.add(token)


def seed_default_users(db: Session) -> None:
    """
    Bootstraps default admin, analyst, and viewer users from environment variables
    if no admin user exists in the database.
    """
    admin_count = db.query(User).filter(User.role == "admin").count()
    if admin_count == 0:
        admin_email = os.getenv("INITIAL_ADMIN_EMAIL", "admin@healthcare.local")
        admin_password = os.getenv("INITIAL_ADMIN_PASSWORD", "AdminSecure#2026!")
        admin_user = User(
            email=admin_email,
            name="System Administrator",
            hashed_password=hash_password(admin_password),
            role="admin",
            status="active"
        )
        db.add(admin_user)

        analyst_email = os.getenv("INITIAL_ANALYST_EMAIL", "analyst@healthcare.local")
        analyst_password = os.getenv("INITIAL_ANALYST_PASSWORD", "AnalystSecure#2026!")
        analyst_user = User(
            email=analyst_email,
            name="Clinical Data Analyst",
            hashed_password=hash_password(analyst_password),
            role="analyst",
            status="active"
        )
        db.add(analyst_user)

        viewer_email = os.getenv("INITIAL_VIEWER_EMAIL", "viewer@healthcare.local")
        viewer_password = os.getenv("INITIAL_VIEWER_PASSWORD", "ViewerSecure#2026!")
        viewer_user = User(
            email=viewer_email,
            name="Auditor & Viewer",
            hashed_password=hash_password(viewer_password),
            role="viewer",
            status="active"
        )
        db.add(viewer_user)
        db.commit()

    # Seed active dataset metadata if absent
    dataset_entry = db.query(ActiveDataset).first()
    if not dataset_entry:
        count = db.query(FactEncounter).count()
        new_ds = ActiveDataset(
            name="UCI Diabetes 130-US Hospitals",
            source="UCI Machine Learning Repository (Inpatient Encounters)",
            record_count=count,
            date_range="1999–2008 Inpatient Admissions",
            is_active=1 if count > 0 else 0
        )
        db.add(new_ds)
        db.commit()

    # Seed model registry entry if absent
    model_entry = db.query(ModelArtifact).first()
    if not model_entry:
        metrics_json = json.dumps({
            "accuracy": 0.615,
            "precision": 0.613,
            "recall": 0.577,
            "f1": 0.595,
            "roc_auc": 0.661
        })
        new_model = ModelArtifact(
            name="readmission_pipeline_v1.joblib",
            version="v1.0",
            is_active=1,
            metrics=metrics_json,
            activated_by="system"
        )
        db.add(new_model)
        db.commit()
