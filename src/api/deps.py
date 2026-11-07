"""
API Dependency Injection Providers
"""
from typing import Generator
from sqlalchemy.orm import Session
from src.warehouse.db import SessionLocal


def get_db_session() -> Generator[Session, None, None]:
    """Provide a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
