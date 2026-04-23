from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from ravioli.backend.core.config import settings
from typing import Generator

# Create engine with PostgreSQL URL
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Check connection liveness before using it
)

# SessionLocal class for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    Ensures the session is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
