"""
Healthcare Data Warehouse Database Engine & Session Factory
Supports SQLite (local zero-dependency development/testing) and Azure SQL/PostgreSQL via DATABASE_URL.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DEFAULT_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../healthcare_dw.db"))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

Base = declarative_base()

# Configure engine with connect_args for SQLite threading support
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency generator for API sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine=None):
    """Create all star schema tables if they do not exist and seed default accounts."""
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)

    # Seed users and active dataset metadata
    from src.security.auth import seed_default_users
    db = SessionLocal()
    try:
        seed_default_users(db)
    except Exception:
        pass
    finally:
        db.close()
