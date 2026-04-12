# GolfCoach AI — Windows Setup Guide

Step-by-step instructions for running the **React + FastAPI** GolfCoach AI on Windows 10/11.

---

## Prerequisites

| Tool | Download |
|------|---------|
| Miniconda or Anaconda | https://docs.conda.io/en/latest/miniconda.html |
| Node.js 18+ | https://nodejs.org/en/download |
| Git | https://git-scm.com/download/win |

---

## Step 1 — Clone the repository

Open **PowerShell** or **Anaconda Prompt**:

```powershell
git clone https://github.com/zainulabidin776/golf-dashboard.git
cd golf-dashboard
```

---

## Step 2 — Create the Python environment

```powershell
conda create -n golfpose python=3.10 -y
conda activate golfpose
```

---

## Step 3 — Install Python dependencies

Install backend API packages (FastAPI, auth, database):

```powershell
pip install -r backend/requirements_api.txt
```

Install core ML & video processing packages:

```powershell
pip install -r requirements.txt
```

**Verify key packages:**

```powershell
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

> ⚠️ **Note:** Database file (`golf.db`) will be auto-created on first backend startup in the project root directory.

---

## Step 4 — Install frontend dependencies

```powershell
cd frontend
npm install
cd ..
```

---

## Step 5 — Start the application

### Option A: One-click launcher (recommended)

```powershell
powershell -ExecutionPolicy Bypass -File start_app.ps1
```

This starts both the backend (port 8000) and frontend (port 5173) automatically.

### Option B: Manual (two terminals)

**Terminal 1 — Backend:**

```powershell
conda activate golfpose
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 — Frontend:**

```powershell
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

```powershell
# Check database exists
Test-Path golf.db

# List tables (requires sqlite3 tools, optional)
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
c:\Users\YourUsername\OneDrive\Desktop\golf-dashboard\golf.db
```

### User Data Stored
- Email, hashed password (argon2), display name, handicap, avatar
- All passwords hashed with argon2-cffi (never stored in plain text)
### First-Time Setup
```powershell
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

# Start (two terminals or one-click)
# Option 1: powershell -ExecutionPolicy Bypass -File start_app.ps1
# Option 2: Terminal 1: python -m uvicorn backend.main:app --port 8000 --reload
#           Terminal 2: cd frontend && npm run dev
```

### Every Session After
```powershell
conda activate golfpose

# Option 1: One-click (recommended)
powershell -ExecutionPolicy Bypass -File start_app.ps1

# Option 2: Manual (two terminals)
# Terminal 1:
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2:
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
| Vite | 8.x | Dev serverte golfpose
pip install -r requirements.txt
```

### ❌ Backend startup fails — sklearn/cv2/mediapipe not found
These ML packages are **only loaded at analysis time**, not at startup. The startup script only checks `fastapi` and `uvicorn`. If you see this error, make sure you're in the `golfpose` conda environment.

### ❌ Ball tracking shows "Not Available"
Place the trained `ball_detector.pt` file in the `models/` directory and set `module3.enabled: true` in `config.yaml`.

### ❌ Frontend build errors
```powershell
cd frontend
npm install
npm run build
```
If TypeScript errors appear, ensure Node.js is 18+:
```powershell
node --version   # Should be v18.x or higher
```

### ❌ Port already in use
```powershell
# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Kill process on port 5173
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

---

## Quick Reference

```powershell
# One-time setup
conda create -n golfpose python=3.10 -y
conda activate golfpose
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Every session
conda activate golfpose
powershell -ExecutionPolicy Bypass -File start_app.ps1
# App at http://localhost:5173
```

---

## Environment Details

| Component | Version |
|-----------|---------|
| Python | 3.10 (via conda `golfpose` env) |
| mediapipe | 0.10.21 (pinned — provides `mp.solutions`) |
| torch | 2.0+ |
| ultralytics | 8.0+ (YOLOv8 for ball detection) |
| fastapi | 0.115+ |
| uvicorn | latest |
| Node.js | 18+ |
| React | 19 |
| Vite | 8.x |
