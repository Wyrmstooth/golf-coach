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

# Verify the ball tracking model is a real file (not a Git LFS pointer).
# Git LFS pointer files are ~130 bytes and start with "version ".
# If the model is missing or is a pointer, warn but don't fail the build.
RUN python3 -c "\
import os; \
model = 'models/golf_ball_frcnn.pt'; \
if not os.path.exists(model): \
    print('WARNING: Ball tracking model not found — ball tracking will be unavailable'); \
elif os.path.getsize(model) < 1000: \
    print('WARNING: Ball tracking model appears to be a Git LFS pointer — run \"git lfs pull\" before building'); \
else: \
    print(f'Ball tracking model OK ({os.path.getsize(model)//1024//1024} MB)')"

EXPOSE 8000

# Run the backend server
CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
