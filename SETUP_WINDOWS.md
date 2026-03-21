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

```powershell
pip install -r requirements.txt
```

**Verify key packages:**

```powershell
python -c "import mediapipe as mp; print('MediaPipe:', mp.__version__)"
python -c "import fastapi; print('FastAPI OK')"
python -c "import torch; print('PyTorch:', torch.__version__)"
```

Expected output:
```
MediaPipe: 0.10.21
FastAPI OK
PyTorch: 2.x.x
```

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

## Step 6 — Open the app

Open your browser at **http://localhost:5173**

---

## Common Issues on Windows

### ❌ `OSError: [WinError 6] The handle is invalid` during analysis
**Cause:** tqdm writing to an invalid stderr handle inside uvicorn's thread.  
**Status:** Already fixed — `_safe_tqdm()` in `video_processor.py` handles this.

### ❌ Analysis stuck at 88% (annotated video generation hangs)
**Cause:** `avc1` (libopenh264) selected as codec but has wrong library version, causing `out.release()` to deadlock.  
**Status:** Already fixed — `mp4v` codec is now tried first in `video_processor.py`.

### ❌ `module 'mediapipe' has no attribute 'solutions'`
The wrong Python environment is active.
```powershell
conda activate golfpose
python -c "import mediapipe as mp; print(hasattr(mp, 'solutions'))"
# Must print: True
```

### ❌ `ModuleNotFoundError` on backend start
```powershell
conda activate golfpose
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
