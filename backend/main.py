"""
GolfCoach FastAPI Backend
Run from the golf_optimized/ root directory:
    uvicorn backend.main:app --reload --port 8000
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# Ensure the project root (golf_optimized/) is on sys.path so all existing
# Python modules (analyze_video, utils, models, etc.) are importable.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routers import analysis as analysis_router
from backend.routers import live as live_router

import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("golfcoach")

app = FastAPI(
    title="GolfCoach API",
    description="REST + WebSocket API that wraps the GolfCoach Python analysis pipeline.",
    version="2.0.0",
)

# Allow the React dev server (and production build) to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # CRA fallback
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve output files (plots, annotated videos, CSVs) as static assets
output_dir = ROOT / "output"
output_dir.mkdir(exist_ok=True)
app.mount("/output", StaticFiles(directory=str(output_dir)), name="output")

app.include_router(analysis_router.router, prefix="/api")
app.include_router(live_router.router, prefix="/api")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    if duration > 1.0:  # Only log slow requests
        logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration:.2f}s)")
    return response


@app.get("/api/health")
async def health() -> dict:
    from backend.job_store import job_store
    jobs = job_store.list_jobs()
    running = sum(1 for j in jobs if j["status"] == "running")
    return {
        "status": "ok",
        "version": "2.0.0",
        "active_jobs": running,
        "total_jobs": len(jobs),
    }
