"""
GolfCoach FastAPI Backend
Run from the golf_optimized/ root directory:
    uvicorn backend.main:app --reload --port 8000
"""
from __future__ import annotations

# ============================================================================
# CRITICAL: Set non-GUI matplotlib backend BEFORE any matplotlib imports
# This prevents "main thread is not in main loop" tkinter errors in FastAPI
# uvicorn workers (which run in non-main threads).
# ============================================================================
import matplotlib
matplotlib.use('Agg')

# Prevent PIL from trying to use tkinter display
import os
os.environ['MPLBACKEND'] = 'Agg'

# Disable PIL image display for headless environments
try:
    from PIL import ImageFile
    ImageFile.LOAD_TRUNCATED_IMAGES = True
except ImportError:
    pass

import sys
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
from backend.routers import auth as auth_router
from backend.routers import sessions as sessions_router
from backend.database import init_db

import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("golfcoach")

app = FastAPI(
    title="GolfCoach API",
    description="REST + WebSocket API that wraps the GolfCoach Python analysis pipeline.",
    version="2.0.0",
)

# Initialise database tables on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Get allowed origins from environment or use defaults
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
).split(",")

# Add middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve output files (plots, annotated videos, CSVs) as static assets
output_dir = ROOT / "output"
output_dir.mkdir(exist_ok=True)
app.mount("/output", StaticFiles(directory=str(output_dir)), name="output")

# Register API routers BEFORE the SPA catch-all static mount
app.include_router(analysis_router.router, prefix="/api")
app.include_router(live_router.router, prefix="/api")
app.include_router(auth_router.router, prefix="/api")
app.include_router(sessions_router.router, prefix="/api")

# Serve frontend static files in production — MUST be AFTER API routers
# (mounting "/" as StaticFiles catches all unmatched routes, so /api would 405)
frontend_dist = ROOT / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")


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
