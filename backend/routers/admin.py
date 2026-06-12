"""Admin router — user management, system stats, job oversight."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import User, SwingSession
from backend.schemas import (
    UserOut, AdminUserUpdate, AdminStats, AdminSessionOut
)
from backend.auth import get_current_admin
from backend.job_store import job_store

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_GUARD = Depends(get_current_admin)


@router.get("/stats", response_model=AdminStats)
def get_admin_stats(db: Session = Depends(get_db), _=ADMIN_GUARD):
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    admin_users = db.query(func.count(User.id)).filter(User.is_admin == True).scalar() or 0
    total_sessions = db.query(func.count(SwingSession.id)).scalar() or 0

    avg_score = db.query(func.avg(SwingSession.overall_score)) \
        .filter(SwingSession.overall_score.isnot(None)).scalar()
    avg_score_all = round(avg_score, 1) if avg_score else None

    jobs = job_store.list_jobs()
    active_jobs = sum(1 for j in jobs if j["status"] == "running")

    return AdminStats(
        total_users=total_users,
        active_users=active_users,
        admin_users=admin_users,
        total_sessions=total_sessions,
        avg_score_all=avg_score_all,
        active_jobs=active_jobs,
        total_jobs=len(jobs),
    )


@router.get("/users", response_model=list[UserOut])
def list_users(
    search: str = Query("", max_length=100),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=ADMIN_GUARD,
):
    q = db.query(User)
    if search:
        q = q.filter(
            User.email.ilike(f"%{search}%") | User.display_name.ilike(f"%{search}%")
        )
    rows = q.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    return [UserOut.model_validate(r) for r in rows]


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _=ADMIN_GUARD,
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: AdminUserUpdate,
    db: Session = Depends(get_db),
    _=ADMIN_GUARD,
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.display_name is not None:
        user.display_name = body.display_name
    if body.handicap is not None:
        user.handicap = body.handicap
    if body.is_admin is not None:
        user.is_admin = body.is_admin
    if body.is_active is not None:
        user.is_active = body.is_active

    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _=ADMIN_GUARD,
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()


@router.get("/sessions", response_model=list[AdminSessionOut])
def list_all_sessions(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _=ADMIN_GUARD,
):
    rows = (
        db.query(SwingSession)
        .join(User)
        .order_by(SwingSession.created_at.desc())
        .limit(limit)
        .all()
    )
    result = []
    for s in rows:
        result.append(AdminSessionOut(
            id=s.id,
            user_id=s.user_id,
            user_name=s.user.display_name if s.user else "Unknown",
            user_email=s.user.email if s.user else "",
            video_filename=s.video_filename,
            overall_score=s.overall_score,
            swing_quality=s.swing_quality,
            faults=s.faults,
            job_id=s.job_id,
            created_at=s.created_at,
        ))
    return result


@router.get("/jobs", response_model=list[dict])
def list_all_jobs(_=ADMIN_GUARD):
    """List all analysis jobs with full details."""
    return job_store.list_jobs()


@router.get("/user-stats/{user_id}")
def get_user_stats(
    user_id: int,
    db: Session = Depends(get_db),
    _=ADMIN_GUARD,
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sessions = (
        db.query(SwingSession)
        .filter(SwingSession.user_id == user_id)
        .order_by(SwingSession.created_at.asc())
        .all()
    )
    scores = [s.overall_score for s in sessions if s.overall_score is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else None
    best_score = round(min(scores), 1) if scores else None

    all_faults = []
    for s in sessions:
        all_faults.extend(s.faults)
    fault_counts = Counter(all_faults).most_common(5)

    score_trend = [
        {"date": s.created_at.strftime("%b %d"), "score": round(s.overall_score, 1)}
        for s in sessions[-20:] if s.overall_score is not None
    ]

    return {
        "user_id": user_id,
        "total_sessions": len(sessions),
        "avg_score": avg_score,
        "best_score": best_score,
        "score_trend": score_trend,
        "top_faults": [{"fault": f, "count": c} for f, c in fault_counts],
    }
