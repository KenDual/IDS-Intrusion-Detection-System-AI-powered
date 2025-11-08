"""
Database configuration and session management for IDS Project
SQLite database with SQLAlchemy ORM
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Database file path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / "ids_database.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create SQLAlchemy engine
# check_same_thread=False is needed for SQLite with FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Set to True for SQL query logging during development
)


# Enable foreign key constraints for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints in SQLite"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()


# Dependency for FastAPI routes
def get_db():
    """
    Database session dependency for FastAPI
    Usage in routes:
        def some_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """
    Initialize database - create all tables
    Should be called on application startup
    """
    from app.models import alert, training_log, whitelist, blacklist, system_config

    Base.metadata.create_all(bind=engine)
    print(f"✓ Database initialized at: {DATABASE_PATH}")


def reset_database():
    """
    Drop all tables and recreate
    WARNING: This will delete all data!
    Use only in development
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print(f"✓ Database reset completed at: {DATABASE_PATH}")


def get_database_info():
    """Get database information"""
    return {
        "database_path": str(DATABASE_PATH),
        "database_url": DATABASE_URL,
        "database_exists": DATABASE_PATH.exists(),
        "database_size_mb": round(DATABASE_PATH.stat().st_size / (1024 * 1024), 2) if DATABASE_PATH.exists() else 0
    }