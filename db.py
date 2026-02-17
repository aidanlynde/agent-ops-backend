import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Production with Postgres (Railway)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")
    engine = create_engine(DATABASE_URL)
else:
    # Local development with SQLite
    SQLITE_DATABASE_URL = "sqlite:///./agent_ops.db"
    engine = create_engine(SQLITE_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db_session():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    from models import Job, Output  # Import here to avoid circular imports
    Base.metadata.create_all(bind=engine)