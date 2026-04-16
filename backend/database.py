"""
Database setup using SQLAlchemy 2.0 (synchronous, thread-scoped sessions).
Supports both SQLite (local dev) and PostgreSQL (production).
"""
from __future__ import annotations

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Support both PostgreSQL (production) and SQLite (local dev)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{Path(__file__).resolve().parent.parent / 'golf.db'}"
)

# Connection args differ for SQLite vs PostgreSQL
connect_args = {} if "postgresql" in DATABASE_URL else {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # verify connections are alive before using
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they don't exist yet (called at app startup)."""
    from backend import models  # noqa: F401 — ensure models are registered
    Base.metadata.create_all(bind=engine)
