"""Database-backed job store for queued analysis tasks."""
from __future__ import annotations

import json
import time
import shutil
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from backend.database import SessionLocal, init_db
from backend.models import AnalysisJob

JobStatus = Literal["pending", "running", "done", "error"]

# Jobs older than 2 hours are eligible for cleanup
JOB_TTL_SECONDS = 2 * 60 * 60


class JobStore:
    def _run_with_init(self, fn):
        try:
            return fn()
        except OperationalError:
            init_db()
            return fn()

    def create(
        self,
        job_id: str,
        video_path: str,
        *,
        output_dir: str | None = None,
        user_id: int | None = None,
        video_filename: str | None = None,
    ) -> None:
        def _create() -> None:
            with SessionLocal() as db:
                db.add(
                    AnalysisJob(
                        job_id=job_id,
                        user_id=user_id,
                        video_filename=video_filename,
                        video_path=video_path,
                        output_dir=output_dir,
                        status="pending",
                        progress=0,
                    )
                )
                db.commit()

        self._run_with_init(_create)

    def update(self, job_id: str, **kwargs: Any) -> None:
        def _update() -> None:
            with SessionLocal() as db:
                job = self._get_job(db, job_id)
                if job is None:
                    return
                self._apply_updates(job, kwargs)
                db.commit()

        self._run_with_init(_update)

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        def _get() -> Optional[Dict[str, Any]]:
            with SessionLocal() as db:
                job = self._get_job(db, job_id)
                return self._to_dict(job) if job else None

        return self._run_with_init(_get)

    def exists(self, job_id: str) -> bool:
        def _exists() -> bool:
            with SessionLocal() as db:
                return self._get_job(db, job_id) is not None

        return self._run_with_init(_exists)

    def list_jobs(self) -> List[Dict[str, Any]]:
        """Return a summary of all jobs (most recent first)."""
        def _list() -> List[Dict[str, Any]]:
            with SessionLocal() as db:
                jobs = db.query(AnalysisJob).order_by(AnalysisJob.created_at.desc()).all()
                return [self._summary(job) for job in jobs]

        return self._run_with_init(_list)

    def claim_next(self, worker_id: str) -> Optional[Dict[str, Any]]:
        def _claim() -> Optional[Dict[str, Any]]:
            with SessionLocal() as db:
                job = (
                    db.query(AnalysisJob)
                    .filter(AnalysisJob.status == "pending")
                    .order_by(AnalysisJob.created_at.asc())
                    .first()
                )
                if job is None:
                    return None
                job.status = "running"
                job.progress = max(job.progress, 5)
                job.worker_id = worker_id
                db.commit()
                db.refresh(job)
                return self._to_dict(job)

        return self._run_with_init(_claim)

    def delete(self, job_id: str) -> bool:
        def _delete() -> tuple[bool, str | None]:
            with SessionLocal() as db:
                job = self._get_job(db, job_id)
                if job is None:
                    return False, None
                output_dir = job.output_dir
                db.delete(job)
                db.commit()
                return True, output_dir

        deleted, output_dir = self._run_with_init(_delete)
        if output_dir:
            shutil.rmtree(output_dir, ignore_errors=True)
        return deleted

    def cleanup(self) -> int:
        now = time.time()
        def _cleanup() -> int:
            removed = 0
            with SessionLocal() as db:
                jobs = db.query(AnalysisJob).filter(AnalysisJob.status.in_(["done", "error"])).all()
                for job in jobs:
                    created_at = job.created_at.timestamp() if job.created_at else now
                    if now - created_at <= JOB_TTL_SECONDS:
                        continue
                    output_dir = job.output_dir
                    db.delete(job)
                    removed += 1
                    if output_dir:
                        try:
                            p = Path(output_dir)
                            if p.exists():
                                shutil.rmtree(p, ignore_errors=True)
                        except Exception:
                            pass
                db.commit()
            return removed

        return self._run_with_init(_cleanup)

    def _get_job(self, db: Session, job_id: str) -> AnalysisJob | None:
        return db.query(AnalysisJob).filter(AnalysisJob.job_id == job_id).first()

    def _apply_updates(self, job: AnalysisJob, updates: Dict[str, Any]) -> None:
        for key, value in updates.items():
            if key == "report":
                job.report_json = json.dumps(value)
            elif hasattr(job, key):
                setattr(job, key, value)

    def _summary(self, job: AnalysisJob) -> Dict[str, Any]:
        report = job.report
        return {
            "job_id": job.job_id,
            "status": job.status,
            "progress": job.progress,
            "created_at": job.created_at.timestamp() if job.created_at else None,
            "video_path": job.video_path,
            "swing_quality": report.get("fault_analysis", {}).get("swing_quality"),
            "overall_score": report.get("fault_analysis", {}).get("overall_score"),
        }

    def _to_dict(self, job: AnalysisJob) -> Dict[str, Any]:
        return {
            "job_id": job.job_id,
            "status": job.status,
            "progress": job.progress,
            "video_path": job.video_path,
            "video_filename": job.video_filename,
            "report": job.report,
            "report_json": job.report_json,
            "output_dir": job.output_dir,
            "error": job.error,
            "user_id": job.user_id,
            "worker_id": job.worker_id,
            "created_at": job.created_at.timestamp() if job.created_at else None,
        }


# Singleton used across the whole backend process
job_store = JobStore()
