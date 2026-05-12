# ── Stage 1: Clone repo with Git LFS to get the real model file ──
FROM python:3.10-slim AS lfs

RUN apt-get update && apt-get install -y --no-install-recommends git git-lfs && rm -rf /var/lib/apt/lists/*
RUN git lfs install
WORKDIR /repo
RUN git clone --depth 1 https://github.com/zainulabidin776/golf-dashboard.git .

# ── Stage 2: Build the app ──
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OpenCV, MediaPipe, PyTorch, scipy, and H.264 video encoding
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libegl1 \
    libgles2 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libopenblas0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLBACKEND=Agg

# Copy and install requirements (layer caching)
COPY requirements.txt ./requirements.txt
COPY backend/requirements_api.txt ./backend/requirements_api.txt

# Prefer wheels for faster builds — torch/torchvision are large
RUN pip install --no-cache-dir --prefer-binary \
    -r requirements.txt \
    -r backend/requirements_api.txt

# Copy remaining project files (LFS pointers for .pt files)
COPY . .

# Replace LFS pointers with real model files from the git-lfs stage
COPY --from=lfs /repo/models/golf_ball_frcnn.pt /app/models/golf_ball_frcnn.pt

# Verify the ball tracking model is a real file (not a Git LFS pointer).
RUN python3 verify_model.py && rm verify_model.py

EXPOSE 8000

# Run the backend server
CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]