# Backend image for Railway / Render Docker deployment
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

# Copy remaining project files
COPY . .

# Resolve Git LFS pointer for the ball tracking model.
# Docker COPY doesn't pull LFS objects, so we download the real binary
# from GitHub's LFS storage using the batch API.
RUN python3 scripts/resolve_lfs.py && rm -rf scripts

# Verify the ball tracking model is a real file (not a Git LFS pointer).
RUN python3 verify_model.py && rm verify_model.py

EXPOSE 8000

# Run the backend server
CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
