"""Pydantic schemas for request/response validation."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


# ── Auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str
    password: str
    handicap: Optional[float] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("display_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Display name cannot be empty")
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


# ── User ─────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    handicap: Optional[float]
    avatar_initials: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    handicap: Optional[float] = None

    @field_validator("display_name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Display name cannot be empty")
        return v.strip() if v else v


# ── Swing Sessions ────────────────────────────────────────────────────────────

class SwingSessionOut(BaseModel):
    id: int
    video_filename: Optional[str]
    overall_score: Optional[float]
    swing_quality: Optional[str]
    faults: list[str]
    job_id: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_sessions: int
    avg_score: Optional[float]
    best_score: Optional[float]
    recent_sessions: list[SwingSessionOut]
    score_trend: list[dict]           # [{date, score}] for chart
    fault_frequency: list[dict]       # [{fault, count}] for chart
