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

```bash
pip install -r requirements.txt
```

**Verify key packages:**

```bash
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

> **Note:** On Linux, MediaPipe requires `libGL`. If you see `libGL.so not found`:
> ```bash
> sudo apt install -y libgl1-mesa-glx libglib2.0-0
> ```

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

## Step 6 — Open the app

Open your browser at **http://localhost:5173**

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

```bash
# One-time setup
conda create -n golfpose python=3.10 -y
conda activate golfpose
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Every session — Terminal 1 (backend)
conda activate golfpose
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Every session — Terminal 2 (frontend)
cd frontend && npm run dev

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
