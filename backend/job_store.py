"""
In-memory job store for analysis tasks.
Keyed by UUID job_id. Thread-safe via a simple dict + threading.Lock.
Includes automatic cleanup of old jobs to prevent unbounded memory growth.
"""
from __future__ import annotations

import threading
import time
import shutil
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

JobStatus = Literal["pending", "running", "done", "error"]

# Jobs older than 2 hours are eligible for cleanup
JOB_TTL_SECONDS = 2 * 60 * 60
# Maximum number of jobs to keep in memory
MAX_JOBS = 50


class JobStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: Dict[str, Dict[str, Any]] = {}

    def create(self, job_id: str, video_path: str) -> None:
        with self._lock:
            self._store[job_id] = {
                "status": "pending",
                "progress": 0,
                "video_path": video_path,
                "report": None,
                "output_dir": None,
                "error": None,
                "created_at": time.time(),
            }
            # Trigger cleanup if too many jobs
            if len(self._store) > MAX_JOBS:
                self._cleanup_unlocked()

    def update(self, job_id: str, **kwargs: Any) -> None:
        with self._lock:
            if job_id in self._store:
                self._store[job_id].update(kwargs)

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._store.get(job_id)

    def exists(self, job_id: str) -> bool:
        with self._lock:
            return job_id in self._store

    def list_jobs(self) -> List[Dict[str, Any]]:
        """Return a summary of all jobs (most recent first)."""
        with self._lock:
            jobs = []
            for jid, data in self._store.items():
                jobs.append({
                    "job_id": jid,
                    "status": data["status"],
                    "progress": data["progress"],
                    "created_at": data.get("created_at"),
                    "video_path": data.get("video_path"),
                    "swing_quality": (data.get("report") or {}).get("fault_analysis", {}).get("swing_quality"),
                    "overall_score": (data.get("report") or {}).get("fault_analysis", {}).get("overall_score"),
                })
            jobs.sort(key=lambda j: j.get("created_at") or 0, reverse=True)
            return jobs

    def _cleanup_unlocked(self) -> None:
        """Remove expired jobs (must be called while holding self._lock)."""
        now = time.time()
        expired = [
            jid for jid, data in self._store.items()
            if data["status"] in ("done", "error")
            and now - data.get("created_at", now) > JOB_TTL_SECONDS
        ]
        for jid in expired:
            output_dir = self._store[jid].get("output_dir")
            del self._store[jid]
            # Clean up output files on disk (non-blocking best-effort)
            if output_dir:
                try:
                    p = Path(output_dir)
                    if p.exists():
                        shutil.rmtree(p, ignore_errors=True)
                except Exception:
                    pass

    def cleanup(self) -> int:
        """Public cleanup method. Returns number of jobs removed."""
        with self._lock:
            before = len(self._store)
            self._cleanup_unlocked()
            return before - len(self._store)


# Singleton used across the whole backend process
job_store = JobStore()
