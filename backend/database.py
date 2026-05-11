"""
Database setup using SQLAlchemy 2.0 (synchronous, thread-scoped sessions).
Supports both SQLite (local dev) and PostgreSQL (production).
"""
from __future__ import annotations

import os
import logging
from pathlib import Path
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, DeclarativeBase

logger = logging.getLogger("golfcoach")

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
    pool_pre_ping=True,
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


def _migrate_columns() -> None:
    """Add any missing columns to existing tables (safe to run on each startup)."""
    inspector = inspect(engine)

    # ── users table ──
    if "users" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("users")}
        with engine.connect() as conn:
            if "is_admin" not in existing:
                logger.info("Migration: adding users.is_admin column")
                conn.execute(
                    __import__("sqlalchemy").text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
                )
                conn.commit()


def init_db() -> None:
    """Create all tables if they don't exist yet, then run column migrations."""
    from backend import models  # noqa: F401 — ensure models are registered
    Base.metadata.create_all(bind=engine)
    _migrate_columns()
