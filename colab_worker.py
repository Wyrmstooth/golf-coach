"""Remote worker that can run in Google Colab or any Python host with more RAM.

Usage:
  1. Clone this repo into Colab or another machine with enough memory.
  2. Install requirements from requirements.txt and backend/requirements_api.txt.
  3. Set BACKEND_URL and ANALYSIS_WORKER_SECRET in the environment.
  4. Run this file to continuously claim queued jobs and upload results.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Iterable

import requests

from analyze_video import MLSwingAnalyzer

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
WORKER_SECRET = os.getenv("ANALYSIS_WORKER_SECRET", "")
WORKER_ID = os.getenv("WORKER_ID", "colab-worker")
POLL_INTERVAL_SECONDS = int(os.getenv("WORKER_POLL_INTERVAL", "10"))


def _headers() -> dict[str, str]:
    return {"X-Worker-Secret": WORKER_SECRET}


def claim_next_job() -> dict | None:
    response = requests.post(
        f"{BACKEND_URL}/api/worker/jobs/next",
        headers=_headers(),
        data={"worker_id": WORKER_ID},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("job")


def download_job_video(job_id: str, destination: Path) -> None:
    with requests.get(
        f"{BACKEND_URL}/api/worker/jobs/{job_id}/download",
        headers=_headers(),
        stream=True,
        timeout=300,
    ) as response:
        response.raise_for_status()
        with destination.open("wb") as fh:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    fh.write(chunk)


def post_progress(job_id: str, progress: int) -> None:
    response = requests.post(
        f"{BACKEND_URL}/api/worker/jobs/{job_id}/progress",
        headers=_headers(),
        data={"progress": progress},
        timeout=30,
    )
    response.raise_for_status()


def iter_artifacts(output_dir: Path) -> Iterable[tuple[str, tuple[str, object, str]]]:
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".mp4": "video/mp4",
        ".csv": "text/csv",
        ".json": "application/json",
    }
    for path in output_dir.glob("**/*"):
        if not path.is_file():
            continue
        mime_type = mime_types.get(path.suffix.lower(), "application/octet-stream")
        yield ("artifacts", (path.name, path.open("rb"), mime_type))


def upload_success(job_id: str, report: dict, output_dir: Path) -> None:
    files = list(iter_artifacts(output_dir))
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/worker/jobs/{job_id}/complete",
            headers=_headers(),
            data={"report_json": json.dumps(report)},
            files=files,
            timeout=300,
        )
        response.raise_for_status()
    finally:
        for _, (_, file_handle, _) in files:
            file_handle.close()


def upload_failure(job_id: str, error: str) -> None:
    response = requests.post(
        f"{BACKEND_URL}/api/worker/jobs/{job_id}/fail",
        headers=_headers(),
        data={"error": error[:10000]},
        timeout=30,
    )
    response.raise_for_status()


def process_job(job: dict) -> None:
    job_id = job["job_id"]
    tmp_dir = Path(tempfile.mkdtemp(prefix=f"golf-job-{job_id}-"))
    try:
        suffix = Path(job.get("video_filename") or "input.mp4").suffix or ".mp4"
        video_path = tmp_dir / f"input{suffix}"
        output_dir = tmp_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        download_job_video(job_id, video_path)
        post_progress(job_id, 10)

        analyzer = MLSwingAnalyzer()

        def on_progress(progress: int) -> None:
            post_progress(job_id, progress)

        report = analyzer.analyze_video(
            video_path=str(video_path),
            output_dir=str(output_dir),
            verbose=False,
            skip_video_render=False,
            progress_callback=on_progress,
        )
        upload_success(job_id, report, output_dir)
    except Exception as exc:
        upload_failure(job_id, repr(exc))
        raise
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main() -> None:
    if not WORKER_SECRET:
        raise RuntimeError("ANALYSIS_WORKER_SECRET is required")

    while True:
        job = claim_next_job()
        if job is None:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        process_job(job)


if __name__ == "__main__":
    main()