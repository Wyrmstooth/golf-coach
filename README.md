# 🏌️ GolfCoach AI — Professional Golf Swing Analyzer

**AI-powered golf swing analysis using MediaPipe pose estimation, ML fault detection, ball tracking, performance prediction, and real-time feedback — served via a modern React + FastAPI web application with user authentication and swing history tracking.**

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![React](https://img.shields.io/badge/React-19-61dafb.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.33-green.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)

---

## 📋 Table of Contents

1. [Quick Start](#-quick-start) — 5-minute setup
2. [System Requirements](#-system-requirements)
3. [Installation](#-installation)
4. [Running the Application](#-running-the-application)
5. [Features](#-features)
6. [Troubleshooting](#-troubleshooting)
7. [Architecture](#-architecture)

---

## ⚡ Quick Start

**For Windows users (fastest method):**

```powershell
# 1. Install prerequisites (if not already installed)
#    - Python 3.10: https://www.python.org/downloads/
#    - Node.js 18+: https://nodejs.org/
#    - Git: https://git-scm.com/download/win

# 2. Clone and setup
git clone https://github.com/zainulabidin776/golf-dashboard.git
cd golf-dashboard

# 3. Create Python environment
conda create -n golfpose python=3.10 -y
conda activate golfpose

# 4. Install dependencies
pip install -r backend/requirements_api.txt
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 5. Run everything at once
powershell -ExecutionPolicy Bypass -File start_app.ps1
```

Then open **http://localhost:5173** in your browser.

---

## 💻 System Requirements

### Minimum Requirements
- **OS:** Windows 10/11, macOS (Intel/Apple Silicon), or Linux (Ubuntu 20.04+)
- **RAM:** 8 GB (16 GB recommended for video processing)
- **Storage:** 5 GB free space (for models + database)
- **GPU:** Optional (CPU-only is supported; GPU significantly faster)
- **Python:** 3.10+
- **Node.js:** 18.0+

### Download Links
| Tool | Link |
|------|------|
| **Miniconda** (Python) | https://docs.conda.io/projects/miniconda/en/latest/miniconda-install.html |
| **Node.js** | https://nodejs.org/en/download |
| **Git** | https://git-scm.com/download |

---

## 📦 Installation

### 1️⃣ Prerequisites Check

Before starting, verify you have the required tools installed:

```bash
# Check Python
python --version
# Expected: Python 3.10.x or higher

# Check Node.js
node --version
# Expected: v18.x or higher

# Check npm
npm --version
# Expected: 9.x or higher
```

If any are missing, install them using the links in the table above.

---

### 2️⃣ Clone the Repository

```bash
git clone https://github.com/zainulabidin776/golf-dashboard.git
cd golf-dashboard
```

---

### 3️⃣ Create Python Environment

**Windows (using Conda/Miniconda):**
```powershell
conda create -n golfpose python=3.10 -y
conda activate golfpose
```

**macOS/Linux (using Conda):**
```bash
conda create -n golfpose python=3.10 -y
conda activate golfpose
```

**Alternative: Using Python venv (if you don't have Conda):**
```bash
# Windows
python -m venv golfpose
golfpose\Scripts\activate

# macOS/Linux
python3 -m venv golfpose
source golfpose/bin/activate
```

---

### 4️⃣ Install Python Dependencies

Make sure your environment is activated, then run:

```bash
# Install backend API dependencies (FastAPI, database, auth)
pip install -r backend/requirements_api.txt

# Install ML & video processing dependencies
pip install -r requirements.txt
```

**Verify Installation:**
```bash
python -c "import mediapipe; print('✓ MediaPipe OK')"
python -c "import fastapi; print('✓ FastAPI OK')"
python -c "import torch; print('✓ PyTorch OK')"
python -c "import sqlalchemy; print('✓ SQLAlchemy OK')"
```

All checks should show `✓ OK` messages.

---

### 5️⃣ Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

## 🚀 Running the Application

### Option 1: Automated Startup (Windows - Recommended)

```powershell
powershell -ExecutionPolicy Bypass -File start_app.ps1
```

This will:
- ✅ Start the FastAPI backend on `http://localhost:8000`
- ✅ Start the React frontend on `http://localhost:5173`
- ✅ Show you the URLs to access

**Expected Output:**
```
====================================
  GolfCoach AI - Starting Services  
====================================
  Python : C:\Users\...\miniconda3\envs\golfpose\python.exe

✓ Backend starting on http://localhost:8000
✓ Frontend starting on http://localhost:5173
✓ Open your browser: http://localhost:5173
```

Then open your browser to **http://localhost:5173** and start using the app!

---

### Option 2: Manual Startup (All Platforms)

If the automated script doesn't work, start services manually:

**Terminal 1 — Start Backend:**
```bash
# Make sure your conda environment is activated
conda activate golfpose  # or: source golfpose/bin/activate

# Start the FastAPI server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Terminal 2 — Start Frontend:**
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v... ready in ... ms

  ➜  Local:   http://localhost:5173/
```

Then open **http://localhost:5173** in your browser.

---

## 🎯 Features

### Core Analysis Engine
- **6-Phase Swing Detection** — Automatically identifies ADDRESS → BACKSWING → TOP → DOWNSWING → IMPACT → FOLLOW-THROUGH
- **ML Fault Detection** — 92% accuracy fault classifier with severity ratings (Critical/Major/Minor)
- **Performance Prediction** — Estimates ball speed, carry distance, and trajectory
- **Ball Tracking** — YOLOv8 detects and tracks the golf ball
- **Annotated Video** — Original video with pose skeleton overlay, phase labels, and fault highlights
- **PDF Reports** — Generate professional analysis reports

### User Management
- 🔐 User Registration & Login
- 📊 Swing History Tracking
- 📈 Performance Dashboard with Charts
- ⚙️ Profile Management
- 🎥 Live Posture Feedback (Real-time webcam analysis)

### Web Interface
- Modern, responsive React dashboard
- Real-time video upload and analysis
- Animated results with detailed breakdowns
- Charts showing progress and trends
- Mobile-friendly design

---

## 🌐 First Time Usage

### 1. Register an Account
- Click **"Sign Up"** on the landing page
- Enter your email and password
- Click **"Register"**

### 2. Upload a Golf Video
- Go to **"Analyze"** page
- Click **"Choose Video"** and select your golf swing video
- Click **"Analyze"**
- Wait for analysis (typically 30-60 seconds depending on video length)

### 3. View Results
- See the analysis breakdown by phase
- Check detected faults and severity levels
- View ball trajectory and distance estimates
- Watch annotated video playback
- Download PDF report

### 4. Track Progress
- Go to **"Dashboard"** to see all your analyzed swings
- View trends and improvement over time
- Compare fault frequency across sessions

---

## ❌ Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'fastapi'"

**Solution:**
```bash
conda activate golfpose
pip install -r backend/requirements_api.txt -r requirements.txt
```

---

### Problem: "Cannot find Python" when running start_app.ps1

**Solution:**
1. Edit `start_app.ps1` in a text editor
2. Find line with `$CONDA_BASE = ...`
3. Change it to your Conda installation path (e.g., `C:\Users\YourName\anaconda3`)
4. Or use manual startup (Option 2 above)

---

### Problem: "npm: command not found"

**Solution:** Install Node.js from https://nodejs.org/ and restart your terminal

---

### Problem: Frontend can't connect to backend

**Possible causes:**
1. Backend is not running (check Terminal 1 for "Uvicorn running" message)
2. Backend is on wrong port (should be 8000)
3. Firewall blocking port 8000

**Solution:**
- Check both services are running
- If using a different port, update frontend API config in `frontend/src/api/base.ts`

---

### Problem: Analysis fails with "CUDA out of memory"

**Solution:** Your GPU doesn't have enough memory. The system will automatically fall back to CPU. This is slower but will work.

---

### Problem: "Database is locked" error

**Solution:**
```bash
# Stop all running instances of the backend
# Wait 5 seconds
# Delete golf.db (it will be recreated)
rm golf.db
# Restart the backend
```

---

### Problem: Very slow video processing

**Possible causes:**
- CPU-based processing (expected, slower than GPU)
- Antivirus scanning files
- Not enough RAM

**Solution:**
- Close other applications
- Consider adding a GPU if processing large videos frequently

---

## 🗂️ Architecture

```
golf-dashboard/
├── backend/                        # FastAPI REST API
│   ├── main.py                     # App entry point + database init
│   ├── auth.py                     # Authentication & JWT tokens
│   ├── database.py                 # SQLAlchemy setup
│   ├── models.py                   # Database models (User, SwingSession)
│   ├── schemas.py                  # API request/response schemas
│   └── routers/
│       ├── auth.py                 # /api/auth/* endpoints
│       ├── analysis.py             # /api/analyze endpoint
│       └── sessions.py             # /api/sessions endpoint
│
├── frontend/                       # React + Vite + TailwindCSS
│   ├── src/
│   │   ├── pages/                  # Page components (Login, Dashboard, etc.)
│   │   ├── components/             # Reusable UI components
│   │   ├── store/                  # Zustand state management
│   │   └── api/                    # API client functions
│   └── package.json                # NPM dependencies
│
├── utils/                          # ML & video processing
│   ├── video_processor.py          # Video I/O
│   ├── pose_detector.py            # Pose estimation
│   ├── phase_detector.py           # Swing phase detection
│   ├── ball_tracker.py             # Ball detection & tracking
│   └── feature_extractor.py        # ML feature engineering
│
├── models/                         # Pre-trained AI models
│   ├── fault_detector.pt           # Fault detection model
│   ├── performance_predictor.pt    # Distance prediction model
│   ├── ball_detector.pt            # Ball detection model
│   └── pose_landmarker_full.task   # MediaPipe pose model
│
├── requirements.txt                # Python ML dependencies
├── backend/requirements_api.txt    # Python API dependencies
└── start_app.ps1                   # One-click startup script
```

---

## 📞 Support & FAQ

**Q: Can I use this on a Mac?**
A: Yes! Follow the same installation steps. Use `bash` instead of PowerShell for the startup script. Or use Option 2 (Manual Startup) which works on all platforms.

**Q: What video formats are supported?**
A: MP4, MOV, AVI, and other OpenCV-supported formats. Recommended: MP4 with resolution 1080p or better, 30+ FPS.

**Q: How long does analysis take?**
A: Typically 30-60 seconds per video, depending on:
- Video length and resolution
- Processor speed (GPU is 10-20x faster)
- System load

**Q: Can I run this without internet?**
A: Yes! Once installed, the app runs completely offline (except registration/updates).

**Q: How much disk space does this need?**
A: ~2-3 GB for models, ~500MB per stored analysis. Allocate at least 5GB total.

---

## 🔧 Advanced Configuration

### Change API Port
Edit `backend/main.py` or run with custom port:
```bash
python -m uvicorn backend.main:app --port 8001
```

### Change Frontend Port
Edit `frontend/vite.config.ts`:
```typescript
export default {
  server: {
    port: 3000  // change from 5173
  }
}
```

### Enable GPU Acceleration
If you have NVIDIA GPU:
```bash
# Install CUDA-enabled PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

---

## 📄 License

See LICENSE file for details.

---

## 👨‍💻 Contributing

Found a bug? Want to add a feature? Submit an issue or pull request on GitHub!

---

**Happy analyzing! ⛳🎯**
├── analyze_video.py                # Core MLSwingAnalyzer class
├── pose_detector.py                # Standalone pose detection script
├── phase_detector.py               # Standalone phase detection script
├── config.yaml                     # Runtime configuration (thresholds, settings)
├── requirements.txt                # Root Python dependencies
├── golf.db                         # SQLite database (auto-created)
├── .gitignore                      # Git ignore for runtime files
├── SETUP_WINDOWS.md                # Detailed Windows setup
├── SETUP_LINUX.md                  # Detailed Linux setup
├── COMPLETE_SETUP_GUIDE.md         # Comprehensive installation guide
└── README.md                       # This file
```

---

## 📋 Requirements

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10, Ubuntu 18.04, macOS 11 | Windows 11, Ubuntu 22.04, macOS 13+ |
| **Python** | 3.9 | 3.10 or 3.11 |
| **RAM** | 8 GB | 16 GB |
| **GPU** | CPU-only ok | NVIDIA CUDA 11.8+ (for faster inference) |
| **Disk** | 2 GB | 5 GB (for models + outputs) |

### Software

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.9–3.11 | Backend & ML inference |
| **Conda/Miniconda** | Latest | Environment isolation |
| **Node.js** | 18+ | Frontend build system |
| **npm** | 9+ | Frontend package manager |
| **Git** | Any | Version control |

---

## 🚀 Installation & Setup

### Quick Start (Windows)

```powershell
# 1. Clone repository
git clone https://github.com/zainulabidin776/golf-dashboard.git
cd golf-dashboard

# 2. Run one-click setup
powershell -ExecutionPolicy Bypass -File start_app.ps1
```

The script automatically:
- Creates `golfpose` Conda environment
- Installs Python + Node dependencies
- Starts FastAPI backend on port **8000**
- Starts React dev server on port **5173**
- Opens browser to `http://localhost:5173`

> ⚠️ **First time?** This takes 5–10 minutes. Subsequent starts are ~30 seconds.

---

### Manual Setup (Windows & Linux)

#### Step 1: Clone Repository

```bash
git clone https://github.com/zainulabidin776/golf-dashboard.git
cd golf-dashboard
```

#### Step 2: Create Python Environment

**Windows (with Conda):**
```powershell
conda create -n golfpose python=3.11 -y
conda activate golfpose
```

**Linux/macOS:**
```bash
conda create -n golfpose python=3.11 -y
conda activate golfpose
```

#### Step 3: Install Python Dependencies

**Backend API packages:**
```bash
pip install -r backend/requirements_api.txt
```

**Core ML & video processing packages:**
```bash
pip install -r requirements.txt
```

**Verify installation:**
```bash
python -c "import fastapi, mediapipe, torch; print('✓ All core packages installed')"
```

#### Step 4: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

Or with pnpm (faster):
```bash
cd frontend
npm install -g pnpm
pnpm install
cd ..
```

#### Step 5: Start Backend Server

**Terminal 1 — Backend (port 8000):**
```bash
conda activate golfpose
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
conda activate golfpose ; python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

#### Step 6: Start Frontend Dev Server

**Terminal 2 — Frontend (port 5173):**
```bash
cd frontend
npm run dev
```

Expected output:
```
  VITE v8.0.0  ready in 234 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

#### Step 7: Open in Browser

Navigate to **`http://localhost:5173`**

You should see:
- Landing page with "Sign In" button
- Click to navigate to login/registration
- Create account, then upload a swing video to analyze

---

## 🔐 Authentication

### User Registration & Login

1. **Visit** `http://localhost:5173`
2. **Click** "Sign In" → "Create Account"
3. **Fill in:**
   - Email (e.g., `golfer@example.com`)
   - Password (min 8 characters)
   - Display Name
   - Handicap (optional)
4. **Click** "Create Account"
5. **Login** with email/password

### JWT Tokens

- Tokens valid for **7 days**
- Automatically stored in browser localStorage under key `golf-auth`
- Sent with every API request via `Authorization: Bearer {token}` header
- Survives page refreshes

### Backend Auth Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/auth/register` | Create new account |
| `POST` | `/api/auth/login` | Login (returns JWT) |
| `GET` | `/api/auth/me` | Get current user profile |
| `PATCH` | `/api/auth/me` | Update display name, handicap |

---

## 📊 Database

### SQLite Setup

- **Location:** `golf.db` in project root
- **Auto-created** on first backend startup
- **Tables:**
  - `user` — Stores email, hashed password, display name, handicap, avatar initials
  - `swing_session` — Stores analysis results (job_id, scores, faults, report JSON, timestamps)

### Database Location
```
c:\golf-dashboard\golf.db    # Windows
/home/user/golf-dashboard/golf.db    # Linux
```

### View Data

**Option 1 — Programmatic (Python):**
```bash
python -c "
import sqlite3
conn = sqlite3.connect('golf.db')
cursor = conn.cursor()
cursor.execute('SELECT email, display_name FROM user')
for row in cursor.fetchall():
    print(row)
conn.close()
"
```

---

## 🎥 Analyzing a Swing

### Via Web UI (Easiest)

1. **Login** to dashboard
2. **Click** "Analyze Swing"
3. **Upload** MP4 video (30–90 seconds)
4. **Wait** for analysis (30–60 seconds depending on video length)
5. **View** results: score, faults, annotated video, PDF report
6. **Check** Dashboard → Charts update with your swing data

### Via API (Curl)

```bash
# 1. Login and get token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"golfer@example.com","password":"mypassword"}' \
  | jq -r '.access_token')

# 2. Upload video for analysis
curl -X POST http://localhost:8000/api/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@path/to/swing.mp4" \
  | jq '.job_id'  # Save this job_id

# 3. Poll for status
curl http://localhost:8000/api/status?job_id=<job_id> | jq '.'

# 4. Get report
curl http://localhost:8000/api/report?job_id=<job_id> | jq '.'
```

---

## 📦 Python Dependencies

### Production Requirements

**Backend API** (`backend/requirements_api.txt`):
- **FastAPI** — Web framework
- **Uvicorn** — ASGI server
- **SQLAlchemy 2.0** — ORM database
- **python-jose** — JWT token creation/verification
- **passlib + argon2-cffi** — Secure password hashing
- **email-validator** — Email validation
- **aiofiles** — Async file handling
- **python-multipart** — File upload support
- **websockets** — WebSocket support

**Core ML** (`requirements.txt`):
- **MediaPipe** — Pose landmark extraction
- **OpenCV** — Video processing
- **NumPy** — Numerical computing
- **SciPy** — Scientific computing
- **Pandas** — Data manipulation
- **PyTorch** — ML model inference
- **Ultralytics** — YOLO object detection
- **Pillow** — Image processing
- **scikit-learn** — ML utilities
- **matplotlib** — Visualization
- **tqdm** — Progress bars
- **PyYAML** — Config file parsing

### Frontend Dependencies (`frontend/package.json`)
- **React 19** — UI library
- **Vite 8** — Build tool
- **TypeScript** — Type safety
- **React Router 7** — Client-side routing
- **Zustand** — State management
- **Axios** — HTTP client
- **Framer Motion** — Animations
- **Recharts** — Charts & graphs
- **Tailwind CSS** — Utility-first CSS
- **React dropzone** — File upload UI
- **Lucide React** — Icon library

---

## 📝 Configuration

### config.yaml

Edit `config.yaml` to adjust pose detection, camera settings, and phase thresholds:

```yaml
pose_detection:
  model_complexity: 2      # 0=fast, 1=normal, 2=accurate
  min_detection_confidence: 0.5
  min_tracking_confidence: 0.5
  smooth_landmarks: true

camera:
  device_id: 0             # Webcam device
  width: 1280
  height: 720
  fps: 30

phase_detection:
  min_phase_frames: 3      # Stability threshold
  smoothing_window: 5
```

### Environment Variables (Optional)

For production, set in `.env`:

```bash
# Backend
DATABASE_URL=sqlite:///./golf.db
SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=7

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```

---

## 🔍 API Reference

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | `POST` | Register new user |
| `/api/auth/login` | `POST` | Login & get JWT token |
| `/api/auth/me` | `GET` | Get current user profile |
| `/api/auth/me` | `PATCH` | Update user profile |

### Analysis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | `POST` | Upload & analyze swing video |
| `/api/status` | `GET` | Check analysis job status |
| `/api/report` | `GET` | Get detailed analysis report |

### Sessions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions/dashboard` | `GET` | Get user's dashboard statistics |
| `/api/sessions/list` | `GET` | Get user's swing history |
| `/api/sessions/{id}` | `DELETE` | Delete a swing session |

### Live

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/live/frame` | `GET` | Stream webcam frame for posture check |

---

## 🐛 Troubleshooting

### Backend Issues

**Error:** `ModuleNotFoundError: No module named 'fastapi'`
```bash
pip install -r backend/requirements_api.txt -r requirements.txt
```

**Error:** `Address already in use` (port 8000)
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9  # Linux/macOS
netstat -ano | findstr :8000 # Windows (get PID, then taskkill /PID <PID>)
```

**Error:** `401 Unauthorized` on API calls
- Ensure Authorization header is being sent
- Check token is valid (not expired after 7 days)
- Login again to refresh token

### Frontend Issues

**Error:** `npm: command not found`
```bash
# Install Node.js from https://nodejs.org (18+ LTS)
# Then retry: npm install
```

**Error:** `Port 5173 already in use`
```bash
npm run dev -- --port 5174  # Use alternate port
```

### Database Issues

**Error:** `database is locked`
```bash
# Close other connections and restart backend
rm golf.db  # Force recreate on next start
```

**Error:** `no such table: user`
```bash
# Backend should auto-create tables on startup
# Verify: backend/main.py has init_db() call on startup event
```

---

## 📊 Monitoring

### Backend Logs

Check terminal running backend for debug info:
```
INFO:     Application startup complete
INFO:     Analyze endpoint called
INFO:     Analysis complete. Report keys: [...]
✓ Session saved for user 1
```

### Database Inspection

```bash
# List all swings for a user
sqlite3 golf.db "SELECT job_id, overall_score, swing_quality FROM swing_session WHERE user_id = 1;"

# Check user count
sqlite3 golf.db "SELECT COUNT(*) FROM user;"
```

---

## 🛠️ Development

### Running Tests

```bash
# Backend (if tests exist)
pytest backend/tests/

# Frontend
npm run test
```

### Building for Production

**Frontend:**
```bash
cd frontend
npm run build
# Output: dist/ folder with optimized bundle
```

**Backend:**
- Set `SECRET_KEY` in `.env`
- Change `DATABASE_URL` to production database
- Run with production ASGI server (Gunicorn, etc.):
  ```bash
  gunicorn backend.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
  ```

---

## 📄 License

[Your License Here]

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit changes (`git commit -am 'Add my feature'`)
4. Push to branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## 📞 Support

For issues, questions, or feedback:
- 📧 Email: support@golfcoachai.com
- 🐛 GitHub Issues: [golf-dashboard/issues](https://github.com/zainulabidin776/golf-dashboard/issues)
- 💬 Discord: [Community Server](https://discord.gg/golfcoach)

---

**Made with ❤️ for golf enthusiasts everywhere.**

---

## 🏋️ Training Your Own Models

```bash
# 1. Prepare labelled videos in good_swings/ and bad_swings/
# 2. Extract CaddieSet features
python training/create_caddieset_dataset.py

# 3. Train fault detector + performance predictor
python training/train_pytorch_models.py

# 4. Train ball detector (requires YOLO-format labelled frames)
python training/train_ball_detector.py --data datasets/golf_ball/data.yaml
```

---

## 📜 License

MIT License — use and modify freely.

---

## 🙏 Acknowledgments

- **MediaPipe** — Google pose estimation
- **CaddieSet** — Professional golf swing dataset (1757 swings, 126 biomechanical features)
- **PyTorch** — Neural network training & inference
- **Ultralytics YOLOv8** — Ball detection
- **FastAPI** — Backend API framework
- **React + Vite + TailwindCSS** — Frontend
