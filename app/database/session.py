"""
Database session management for AEON
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Database URL - Using SQLite for Phase 1, can be upgraded to PostgreSQL later
DATABASE_URL = "sqlite:///./aeon.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    poolclass=StaticPool,
    echo=settings.debug,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    from .models import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def drop_tables():
    """Drop all database tables (for development)"""
    from .models import Base
    Base.metadata.drop_all(bind=engine)
    logger.info("Database tables dropped successfully") 