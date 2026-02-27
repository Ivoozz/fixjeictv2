from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from .config import settings

# Create SQLAlchemy engine
# For SQLite, use check_same_thread=False and enable WAL mode
if settings.DATABASE_URL.startswith("sqlite:///"):
    # Ensure the directory exists
    db_path = settings.database_path
    if db_path:
        db_path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

# Session factory
SessionLocal = orm.sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database sessions in FastAPI routes.
    Ensures proper cleanup after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions outside of FastAPI routes.
    Use with: with db_session() as db: ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    # Import all models to ensure they're registered
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Enable WAL mode for SQLite (better concurrency)
    if settings.DATABASE_URL.startswith("sqlite:///"):
        with engine.connect() as conn:
            conn.execute(orm.text("PRAGMA journal_mode=WAL"))
            conn.execute(orm.text("PRAGMA synchronous=NORMAL"))
            conn.commit()
