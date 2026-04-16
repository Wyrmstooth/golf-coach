"""Worker router used by external analysis workers such as Google Colab."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from backend.job_store import job_store
from backend.routers.sessions import save_session_for_user

logger = logging.getLogger("golfcoach")

router = APIRouter(prefix="/worker", tags=["worker"])
ROOT = Path(__file__).resolve().parent.parent.parent
WORKER_SECRET = os.getenv("ANALYSIS_WORKER_SECRET", "")


def require_worker_secret(x_worker_secret: str | None = Header(default=None)) -> str:
    if not WORKER_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ANALYSIS_WORKER_SECRET is not configured.",
        )
    if x_worker_secret != WORKER_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid worker secret.")
    return x_worker_secret


def _rewrite_report_paths(report: dict[str, Any], output_dir: str) -> dict[str, Any]:
    saved_files = {path.name: str(path) for path in Path(output_dir).glob("**/*") if path.is_file()}

    def _normalize(value: Any) -> Any:
        if isinstance(value, str):
            name = Path(value).name
            return saved_files.get(name, value)
        return value

    outputs = report.get("outputs", {})
    for key in ("plot", "annotated_video", "ball_plot"):
        if key in outputs:
            outputs[key] = _normalize(outputs.get(key))

    screenshots = outputs.get("phase_screenshots", {}) or {}
    for key, value in list(screenshots.items()):
        screenshots[key] = _normalize(value)

    ball_tracking = report.get("ball_tracking", {}) or {}
    files = ball_tracking.get("files", {}) or {}
    for key, value in list(files.items()):
        files[key] = _normalize(value)

    return report


@router.post("/jobs/next")
def claim_next_job(
    _: str = Depends(require_worker_secret),
    worker_id: str = Form(default="colab-worker"),
):
    job = job_store.claim_next(worker_id)
    if job is None:
        return {"job": None}
    return {
        "job": {
            "job_id": job["job_id"],
            "video_filename": job.get("video_filename"),
            "progress": job.get("progress"),
        }
    }


@router.get("/jobs/{job_id}/download")
def download_job_video(job_id: str, _: str = Depends(require_worker_secret)):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    video_path = job.get("video_path")
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Input video is no longer available.")
    filename = job.get("video_filename") or Path(video_path).name
    return FileResponse(video_path, filename=filename)


@router.post("/jobs/{job_id}/progress")
def update_job_progress(
    job_id: str,
    progress: int = Form(...),
    _: str = Depends(require_worker_secret),
):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    job_store.update(job_id, status="running", progress=max(0, min(progress, 99)))
    return {"detail": "ok"}


@router.post("/jobs/{job_id}/complete")
async def complete_job(
    job_id: str,
    report_json: str = Form(...),
    artifacts: list[UploadFile] = File(default=[]),
    _: str = Depends(require_worker_secret),
):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    output_dir = job.get("output_dir") or str(ROOT / "output" / job_id)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for artifact in artifacts:
        filename = Path(artifact.filename or "artifact.bin").name
        if not filename:
            continue
        target = Path(output_dir) / filename
        with target.open("wb") as fh:
            while chunk := await artifact.read(1024 * 1024):
                fh.write(chunk)

    try:
        report = json.loads(report_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid report_json: {exc}") from exc

    report = _rewrite_report_paths(report, output_dir)
    job_store.update(job_id, status="done", progress=100, report=report, output_dir=output_dir, error=None)

    if job.get("user_id") is not None:
        try:
            from backend.database import SessionLocal

            with SessionLocal() as db:
                save_session_for_user(
                    db,
                    user_id=job["user_id"],
                    job_id=job_id,
                    video_filename=job.get("video_filename") or "",
                    report=report,
                )
        except Exception as exc:
            logger.error("Failed to save session for job %s: %s", job_id, exc, exc_info=True)

    return {"detail": "ok"}


@router.post("/jobs/{job_id}/fail")
def fail_job(
    job_id: str,
    error: str = Form(...),
    _: str = Depends(require_worker_secret),
):
    if not job_store.exists(job_id):
        raise HTTPException(status_code=404, detail="Job not found.")
    job_store.update(job_id, status="error", progress=0, error=error)
    return {"detail": "ok"}