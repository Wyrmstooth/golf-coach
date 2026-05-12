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

# Configurable URL for the ball tracking model (165 MB).
# Set on Railway/Render as env var pointing to the model file.
# Example: MODEL_URL=https://huggingface.co/user/golf-ball-detector/resolve/main/golf_ball_frcnn.pt
ENV MODEL_URL=""

# Copy and install requirements (layer caching)
COPY requirements.txt ./requirements.txt
COPY backend/requirements_api.txt ./backend/requirements_api.txt

# Prefer wheels for faster builds — torch/torchvision are large
RUN pip install --no-cache-dir --prefer-binary \
    -r requirements.txt \
    -r backend/requirements_api.txt

# Copy remaining project files
COPY . .

# Verify model status (warns but does not fail build)
RUN python3 verify_model.py || true; rm -f verify_model.py

EXPOSE 8000

# At container startup: download model if MODEL_URL is set and model not present
# Then start the server
CMD ["sh", "-c", "python3 scripts/download_model.py; python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]