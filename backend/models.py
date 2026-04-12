"""ORM models for the golf dashboard application."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String(255), unique=True, index=True, nullable=False)
    display_name  = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    handicap      = Column(Float, nullable=True)
    avatar_initials = Column(String(4), nullable=True)  # e.g. "JD"
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sessions = relationship("SwingSession", back_populates="user", cascade="all, delete-orphan")


class SwingSession(Base):
    __tablename__ = "swing_sessions"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    video_filename  = Column(String(255), nullable=True)
    overall_score   = Column(Float, nullable=True)
    swing_quality   = Column(String(50), nullable=True)  # "Good", "Average", "Poor"
    faults_json     = Column(Text, nullable=True)   # JSON array of fault names
    report_json     = Column(Text, nullable=True)   # Full analysis report JSON
    job_id          = Column(String(100), nullable=True, index=True)
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="sessions")

    # ── convenience helpers ───────────────────────────────────────────────────

    @property
    def faults(self) -> list[str]:
        if not self.faults_json:
            return []
        try:
            return json.loads(self.faults_json)
        except Exception:
            return []

    @property
    def report(self) -> dict:
        if not self.report_json:
            return {}
        try:
            return json.loads(self.report_json)
        except Exception:
            return {}
