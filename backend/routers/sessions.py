"""Sessions router — list, get, delete user swing sessions + dashboard stats."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, SwingSession
from backend.schemas import SwingSessionOut, DashboardStats
from backend.auth import get_current_user

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/", response_model=list[SwingSessionOut])
def list_sessions(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(SwingSession)
        .filter(SwingSession.user_id == current_user.id)
        .order_by(SwingSession.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_to_out(r) for r in rows]


@router.get("/dashboard", response_model=DashboardStats)
def dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = (
        db.query(SwingSession)
        .filter(SwingSession.user_id == current_user.id)
        .order_by(SwingSession.created_at.asc())
        .all()
    )

    scores = [s.overall_score for s in sessions if s.overall_score is not None]
    avg_score  = round(sum(scores) / len(scores), 1) if scores else None
    best_score = round(max(scores), 1) if scores else None

    # Score trend for chart — last 20 sessions with a score
    trend_sessions = [s for s in sessions if s.overall_score is not None][-20:]
    score_trend = [
        {
            "date": s.created_at.strftime("%b %d"),
            "score": round(s.overall_score, 1),
        }
        for s in trend_sessions
    ]

    # Fault frequency
    all_faults: list[str] = []
    for s in sessions:
        all_faults.extend(s.faults)
    fault_counts = Counter(all_faults).most_common(8)
    fault_frequency = [{"fault": f, "count": c} for f, c in fault_counts]

    recent = [_to_out(s) for s in reversed(sessions[-10:])]

    return DashboardStats(
        total_sessions=len(sessions),
        avg_score=avg_score,
        best_score=best_score,
        recent_sessions=recent,
        score_trend=score_trend,
        fault_frequency=fault_frequency,
    )


@router.get("/{session_id}", response_model=SwingSessionOut)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = db.get(SwingSession, session_id)
    if not s or s.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return _to_out(s)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = db.get(SwingSession, session_id)
    if not s or s.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    db.delete(s)
    db.commit()


# ── Internal helper used by analysis router ───────────────────────────────────

def save_session_for_user(
    db: Session,
    user_id: int,
    *,
    job_id: str,
    video_filename: str,
    report: dict,
) -> SwingSession:
    """Called after analysis completes to persist results for a logged-in user."""
    existing = (
        db.query(SwingSession)
        .filter(SwingSession.user_id == user_id, SwingSession.job_id == job_id)
        .first()
    )

    # Try nested structure first (fault_analysis), then flat structure for backwards compat
    fault_analysis = report.get("fault_analysis", {})
    score        = fault_analysis.get("overall_score") or report.get("overall_score") or report.get("swing_score")
    quality      = fault_analysis.get("swing_quality") or report.get("swing_quality") or report.get("quality_label")
    
    # Get faults from fault_details or top-level
    faults_raw   = []
    if "fault_details" in fault_analysis and isinstance(fault_analysis["fault_details"], dict):
        faults_raw = fault_analysis["fault_details"].get("faults", [])
    if not faults_raw:
        faults_raw = report.get("faults_detected") or report.get("faults") or []
    
    # Extract fault names from FaultDetail objects
    fault_names: list[str] = []
    for f in faults_raw:
        if isinstance(f, str):
            fault_names.append(f)
        elif isinstance(f, dict):
            # FaultDetail has "title" field
            fault_name = f.get("title") or f.get("name") or f.get("fault") or str(f)
            fault_names.append(fault_name)

    s = existing or SwingSession(user_id=user_id, job_id=job_id)
    s.video_filename = video_filename
    s.overall_score = float(score) if score is not None else None
    s.swing_quality = str(quality) if quality else None
    s.faults_json = json.dumps(fault_names)
    s.report_json = json.dumps(report)
    if existing is None:
        db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _to_out(s: SwingSession) -> SwingSessionOut:
    return SwingSessionOut(
        id=s.id,
        video_filename=s.video_filename,
        overall_score=s.overall_score,
        swing_quality=s.swing_quality,
        faults=s.faults,
        job_id=s.job_id,
        created_at=s.created_at,
    )
