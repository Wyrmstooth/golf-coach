"""
In-memory job store for analysis tasks.
Keyed by UUID job_id. Thread-safe via a simple dict + threading.Lock.
"""
from __future__ import annotations

import threading
from typing import Any, Dict, Literal, Optional

JobStatus = Literal["pending", "running", "done", "error"]


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
            }

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


# Singleton used across the whole backend process
job_store = JobStore()
