"""
Analysis router – wraps MLSwingAnalyzer in background threads.

Endpoints:
  POST   /api/analyze                  Upload video, start analysis job
  GET    /api/status/{job_id}          Poll job progress
  GET    /api/report/{job_id}          Fetch completed JSON report
  GET    /api/files/{job_id}/{filename} Serve output files (PNG, MP4, CSV)
"""
from __future__ import annotations

import os
import shutil
import sys
import uuid
import tempfile
import traceback
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse

from backend.auth import get_optional_user
from backend.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger("golfcoach")

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# ---- Guard: mediapipe Tasks API is broken on Python 3.12+ ----
import sys as _sys
if _sys.version_info >= (3, 12):
    import warnings
    warnings.warn(
        f"WARNING: Backend is running on Python {_sys.version_info.major}.{_sys.version_info.minor} "
        "(base conda env). MediaPipe requires Python 3.10.\n"
        "Start the backend with:\n"
        "  & \"$env:USERPROFILE\\miniconda3\\envs\\golfpose\\python.exe\" "
        "-m uvicorn backend.main:app --reload --port 8000",
        stacklevel=1,
    )

from backend.job_store import job_store

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=2)


def _recover_job_from_disk(job_id: str) -> dict | None:
    """
    Reconstruct a completed job entry from files saved on disk.
    Called when job_id is missing from the in-memory store (e.g. after a hot-reload).
    Returns a minimal job dict if the output directory exists, else None.
    """
    output_dir = ROOT / "output" / job_id
    if not output_dir.is_dir():
        return None
    report_files = sorted(output_dir.glob("*_report.json"))
    if not report_files:
        # Dir exists but no report yet → job may still be running in another process
        return None
    import json
    try:
        with open(report_files[0]) as fh:
            report = json.load(fh)
    except Exception:
        report = None
    return {
        "status": "done",
        "progress": 100,
        "video_path": "",
        "report": report,
        "output_dir": str(output_dir),
        "error": None,
    }

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB


def _run_analysis(
    job_id: str,
    video_path: str,
    output_dir: str,
    user_id: int | None = None,
    video_filename: str = "",
) -> None:
    """
    Blocking analysis function executed in a thread-pool worker.
    Imports MLSwingAnalyzer here to avoid loading heavy models on startup.
    """
    try:
        job_store.update(job_id, status="running", progress=5)

        from analyze_video import MLSwingAnalyzer  # type: ignore

        job_store.update(job_id, progress=10)

        analyzer = MLSwingAnalyzer()
        job_store.update(job_id, progress=20)

        def _on_progress(pct: int) -> None:
            """Relay granular progress from analyze_video() into the job store."""
            job_store.update(job_id, progress=pct)

        report = analyzer.analyze_video(
            video_path=video_path,
            output_dir=output_dir,
            verbose=False,
            skip_video_render=False,
            progress_callback=_on_progress,
        )
        job_store.update(
            job_id,
            status="done",
            progress=100,
            report=report,
            output_dir=output_dir,
        )

        logger.info(f"Analysis complete. Report keys: {list(report.keys()) if isinstance(report, dict) else 'not a dict'}")
        logger.info(f"User ID: {user_id}, Video: {video_filename}")

        # Persist session for authenticated users
        if user_id is not None:
            try:
                from backend.database import SessionLocal
                from backend.routers.sessions import save_session_for_user
                with SessionLocal() as db:
                    save_session_for_user(
                        db,
                        user_id=user_id,
                        job_id=job_id,
                        video_filename=video_filename,
                        report=report,
                    )
                logger.info(f"✓ Session saved for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to save session: {e}", exc_info=True)

    except Exception:
        job_store.update(
            job_id,
            status="error",
            progress=0,
            error=traceback.format_exc(),
        )


@router.post("/analyze")
async def analyze_video(
    file: UploadFile = File(...),
    current_user=Depends(get_optional_user),
) -> Dict[str, str]:
    """
    Accept a multipart video upload, save it, kick off background analysis,
    and return the job_id for polling.
    """
    logger.info(f"Analyze endpoint called. Current user: {current_user}")
    if current_user:
        logger.info(f"  User ID: {current_user.id}, Email: {current_user.email}")
    else:
        logger.info("  No user logged in (anonymous analysis)")
    
    suffix = Path(file.filename or "video.mp4").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {ALLOWED_EXTENSIONS}",
        )

    job_id = str(uuid.uuid4())
    output_dir = str(ROOT / "output" / job_id)
    os.makedirs(output_dir, exist_ok=True)

    # Save uploaded file with streaming to avoid loading full file into memory
    video_path = os.path.join(output_dir, f"input{suffix}")
    total_size = 0
    with open(video_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                f.close()
                os.remove(video_path)
                raise HTTPException(status_code=413, detail="File too large (max 500 MB).")
            f.write(chunk)

    job_store.create(job_id, video_path)
    job_store.update(job_id, output_dir=output_dir)

    # Submit to thread pool (non-blocking for the event loop)
    user_id = current_user.id if current_user else None
    executor.submit(
        _run_analysis,
        job_id,
        video_path,
        output_dir,
        user_id,
        file.filename or "",
    )

    return {"job_id": job_id}


@router.get("/status/{job_id}")
async def get_status(job_id: str) -> Dict[str, Any]:
    """Return current job status and progress (0–100)."""
    job = job_store.get(job_id) or _recover_job_from_disk(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "error": job.get("error"),
    }


@router.get("/report/{job_id}")
async def get_report(job_id: str) -> Any:
    """Return the full JSON report once the job is done."""
    job = job_store.get(job_id) or _recover_job_from_disk(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job["status"] != "done":
        raise HTTPException(
            status_code=202,
            detail=f"Job is '{job['status']}'. Poll /api/status/{job_id} first.",
        )
    return JSONResponse(content=job["report"])


@router.get("/files/{job_id}/{filename}")
async def get_file(job_id: str, filename: str) -> FileResponse:
    """Serve output files produced by the analysis (PNG, MP4, CSV, JSON)."""
    job = job_store.get(job_id) or _recover_job_from_disk(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    output_dir = job.get("output_dir")
    if not output_dir:
        raise HTTPException(status_code=404, detail="No output directory for this job.")

    # SECURITY: Prevent path traversal attacks
    safe_dir = Path(output_dir).resolve()
    file_path = (safe_dir / filename).resolve()
    if not str(file_path).startswith(str(safe_dir)):
        raise HTTPException(status_code=400, detail="Invalid filename.")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found.")

    # Determine media type
    ext = file_path.suffix.lower()
    media_types = {
        ".mp4": "video/mp4",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".csv": "text/csv",
        ".json": "application/json",
    }
    media_type = media_types.get(ext, "application/octet-stream")
    return FileResponse(str(file_path), media_type=media_type, filename=filename)


@router.get("/history")
async def get_history() -> list:
    """Return a summary of all analysis jobs (most recent first)."""
    return job_store.list_jobs()


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str) -> Dict[str, str]:
    """Delete a completed job and its output files."""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job["status"] == "running":
        raise HTTPException(status_code=409, detail="Cannot delete a running job.")
    output_dir = job.get("output_dir")
    if output_dir:
        import shutil
        shutil.rmtree(output_dir, ignore_errors=True)
    # Remove from store
    with job_store._lock:
        job_store._store.pop(job_id, None)
    return {"detail": "Job deleted."}
