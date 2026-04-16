# Backend image for Render Docker deployment
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OpenCV, MediaPipe, and Python
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1 \
    libegl1 \
    libgles2 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLBACKEND=Agg

# Copy requirements
COPY requirements.txt ./requirements.txt
COPY backend/requirements_api.txt ./backend/requirements_api.txt

# Install Python dependencies
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt -r backend/requirements_api.txt

# Copy project files
COPY . .

EXPOSE 8000

# Run the backend server using Render's injected PORT
CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
