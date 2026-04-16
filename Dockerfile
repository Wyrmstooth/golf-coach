# Multi-stage build for GolfCoach
# Stage 1: Frontend build
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend files
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# Stage 2: Python backend with frontend static files
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OpenCV, MediaPipe, and Python
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLBACKEND=Agg

# Copy requirements
COPY requirements.txt backend/requirements_api.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt -r backend/requirements_api.txt

# Copy project files
COPY . .

# Copy built frontend dist to backend static files
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create a simple static file handler in FastAPI
# The app will serve frontend from /frontend/dist

EXPOSE 8000

# Run the backend server
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
