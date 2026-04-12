# GolfCoach AI — Linux Setup Guide

Step-by-step instructions for running the **React + FastAPI** GolfCoach AI on Ubuntu 20.04+ / Debian / other Linux distros.

---

## Prerequisites

```bash
# Check versions
python3 --version     # Need 3.9–3.11
node --version        # Need 18+
npm --version         # Need 9+
git --version
```

Install missing tools:

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install -y git curl build-essential

# Node.js 18 (via NodeSource)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Miniconda (if not installed)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
source ~/.bashrc
```

---

## Step 1 — Clone the repository

```bash
git clone https://github.com/zainulabidin776/golf-dashboard.git
cd golf-dashboard
```

---

## Step 2 — Create the Python environment

```bash
conda create -n golfpose python=3.10 -y
conda activate golfpose
```

---

## Step 3 — Install Python dependencies

Install backend API packages (FastAPI, auth, database):

```bash
pip install -r backend/requirements_api.txt
```

Install core ML & video processing packages:

```bash
pip install -r requirements.txt
```

**Verify key packages:**

```bash
python -c "import mediapipe as mp; print('✓ MediaPipe:', mp.__version__)"
python -c "import fastapi; print('✓ FastAPI installed')"
python -c "import sqlalchemy; print('✓ SQLAlchemy:', sqlalchemy.__version__)"
python -c "import torch; print('✓ PyTorch:', torch.__version__)"
python -c "import passlib; print('✓ Passlib installed')"
```

Expected output:
```
✓ MediaPipe: 0.10.33
✓ FastAPI installed
✓ SQLAlchemy: 2.x.x
✓ PyTorch: 2.x.x
✓ Passlib installed
```

**Linux-specific dependencies:**

```bash
# Required for MediaPipe on Linux
sudo apt install -y libgl1-mesa-glx libglib2.0-0 libxext6 libsm6

# Optional but recommended
sudo apt install -y sqlite3  # For database inspection
```

> ⚠️ **Note:** Database file (`golf.db`) will be auto-created on first backend startup in the project root directory.

---

## Step 4 — Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

---

## Step 5 — Start the application

### Option A: Run with the shell script

```bash
chmod +x launch_app.sh
./launch_app.sh
```

### Option B: Manual (two terminals)

**Terminal 1 — Backend:**

```bash
conda activate golfpose
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

You should see:
```
VITE v8.x.x  ready in xxxx ms
➜  Local:   http://localhost:5173/
```

---

## Step 6 — Configure Authentication (First Time)

On first backend startup, the app automatically:
- Creates `golf.db` SQLite database in the project root
- Initializes `user` and `swing_session` tables
- Sets up JWT secret key (hardcoded for dev; change in production)

No manual configuration needed — the database is created automatically.

---

## Step 7 — Open the app

Open your browser at **http://localhost:5173**

### First-Time User Flow

1. **Click** "Sign In" → "Create Account"
2. **Register** with:
   - Email: `your@email.com`
   - Password: `SecurePassword123` (min 8 chars)
   - Display Name: `Your Name`
   - Handicap: (optional)
3. **Login** with email/password
4. **Browse** to "Analyze Swing" and upload a golf video
5. **View** results on "Dashboard" after analysis completes

---

## Step 8 — Verify Database Setup

To confirm the database is working:

```bash
# Check database exists
test -f golf.db && echo "✓ Database exists" || echo "✗ Database not found"

# List tables (requires sqlite3)
sqlite3 golf.db "SELECT name FROM sqlite_master WHERE type='table';"

# Expected output:
# user
# swing_session
```

---

## Authentication & Database

### JWT Tokens
- **Expiry:** 7 days
- **Storage:** localStorage (survives page refreshes)
- **Sent as:** `Authorization: Bearer {token}` header with every API request

### Database Location
```
~/golf-dashboard/golf.db
# or
/home/username/path/to/golf-dashboard/golf.db
```

### User Data Stored
- Email, hashed password (argon2), display name, handicap, avatar
- All passwords hashed with argon2-cffi (never stored in plain text)

### Swing Session Data Stored
- Job ID, analysis report (JSON), score, swing quality, detected faults
- Linked to user via `user_id` foreign key

---

## GPU Acceleration (Optional)

For faster analysis with an NVIDIA GPU:

```bash
# Install CUDA-enabled PyTorch (check https://pytorch.org for your CUDA version)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Verify CUDA
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

---

## Running in the Background (Production-like)

Use `screen` or `tmux` to keep services running after closing the terminal:

```bash
# Using screen
screen -S golfcoach-backend
conda activate golfpose
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
# Press Ctrl+A then D to detach

screen -S golfcoach-frontend
cd /path/to/golf-dashboard/frontend
npm run dev
# Press Ctrl+A then D to detach

# List running screens
screen -ls

# Reattach
screen -r golfcoach-backend
```

---

## Common Issues on Linux

### ❌ `libGL.so.1: cannot open shared object file`

```bash
sudo apt install -y libgl1-mesa-glx libglib2.0-0
```

### ❌ `libgomp.so.1: cannot open shared object file`

```bash
sudo apt install -y libgomp1
```

### ❌ `module 'mediapipe' has no attribute 'solutions'`

Wrong Python environment:
```bash
conda activate golfpose
python -c "import mediapipe as mp; print(hasattr(mp, 'solutions'))"
# Must print: True
```

### ❌ `ModuleNotFoundError` on backend start

```bash
conda activate golfpose
pip install -r requirements.txt
```

### ❌ Port already in use

```bash
# Kill process on port 8000
sudo lsof -t -i:8000 | xargs kill -9

# Kill process on port 5173
sudo lsof -t -i:5173 | xargs kill -9
```

### ❌ `ENOSPC: System limit for number of file watchers reached`

```bash
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### ❌ Permission denied on `launch_app.sh`

```bash
chmod +x launch_app.sh setup.sh
```

### ❌ MediaPipe camera access on headless servers

For live webcam features, a display is required. Analysis-only mode works headlessly without any display.

---

## Quick Reference

### First-Time Setup
```bash
# Clone repo
git clone https://github.com/zainulabidin776/golf-dashboard.git
cd golf-dashboard

# Create environment
conda create -n golfpose python=3.11 -y
conda activate golfpose

# Install dependencies (API first, then ML)
pip install -r backend/requirements_api.txt
pip install -r requirements.txt

# Frontend
cd frontend && npm install && cd ..

# Start (two terminals)
# Terminal 1: python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
# Terminal 2: cd frontend && npm run dev
```

### Every Session After
```bash
conda activate golfpose

# Terminal 1 (Backend)
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Terminal 2 (Frontend)
cd frontend && npm run dev

# App at http://localhost:5173
```

---

## Dependency Summary

### Backend API (`backend/requirements_api.txt`)
- `fastapi` — Web framework
- `uvicorn` — ASGI server
- `sqlalchemy>=2.0.0` — Database ORM
- `python-jose` — JWT tokens
- `passlib[argon2]` — Password hashing
- `argon2-cffi` — Argon2 algorithm
- `email-validator` — Email validation

### Core ML (`requirements.txt`)
- `mediapipe>=0.10.33` — Pose detection
- `opencv-python` — Video processing
- `numpy`, `scipy`, `pandas` — Data processing
- `torch`, `torchvision` — ML models
- `ultralytics>=8.0.0` — YOLO ball detection
- `matplotlib` — Visualization
- `pillow` — Image processing

### Frontend (`frontend/package.json`)
- `react@19` — UI framework
- `vite@8` — Build tool
- `typescript` — Type safety
- `zustand` — State management
- `axios` — HTTP client
- `react-router-dom@7` — Routing
- `framer-motion` — Animations
- `recharts` — Charts
- `tailwindcss` — CSS framework

---

## Environment Details

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11 | Backend & ML |
| Conda | Latest | Env management |
| mediapipe | 0.10.33 | Pose landmarks |
| PyTorch | 2.0+ | ML inference |
| FastAPI | 0.110+ | REST API |
| SQLAlchemy | 2.0+ | Database ORM |
| Node.js | 18+ | Frontend build |
| React | 19 | UI library |
| Vite | 8.x | Dev server |
