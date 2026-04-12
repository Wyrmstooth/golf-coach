# 🏌️ GolfCoach AI — Professional Golf Swing Analyzer

**AI-powered golf swing analysis using MediaPipe pose estimation, ML fault detection, ball tracking, performance prediction, and real-time feedback — served via a modern React + FastAPI web application with user authentication and swing history tracking.**

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![React](https://img.shields.io/badge/React-19-61dafb.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.33-green.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)
![Vite](https://img.shields.io/badge/Vite-8.0+-6434c3.svg)
![Tailwind](https://img.shields.io/badge/Tailwind-3.4+-38b0ac.svg)

---

## 🎯 Features

### Core Analysis
- **6-Phase Swing Detection** — ADDRESS → BACKSWING → TOP → DOWNSWING → IMPACT → FOLLOW-THROUGH
- **ML Fault Detection** — 92% accuracy PyTorch classifier with per-phase severity ratings (🔴🟠🟡)
- **Performance Prediction** — Neural network estimating ball speed, distance & carry (R²=0.67)
- **Ball Tracking** — YOLOv8 ball detection + trajectory + distance estimation
- **Annotated Video** — Pose skeleton overlay, phase labels, fault highlights, slow-motion playback
- **PDF Reports** — Downloadable multi-page analysis with per-phase fault tables

### User Features
- **User Authentication** — Email/password registration & login with JWT tokens (7-day expiry)
- **Profile Management** — User dashboard with handicap, display name, avatar
- **Swing History** — Track all analyzed swings with scores, faults, and quality ratings
- **Dashboard Analytics** — Charts showing score trends, fault frequency, and performance metrics
- **Live Posture Check** — Real-time webcam feedback for ADDRESS phase alignment

### Web UI
- **Modern Dashboard** — React 19 + Vite with Framer Motion animations
- **Responsive Design** — Tailwind CSS + mobile-friendly layouts
- **Real-Time Charts** — Recharts for score trends and fault frequency visualization
- **Protected Routes** — Automatic authentication checks and redirects
- **Offline Support** — Auth tokens and user data persisted in localStorage

---

## 🗂️ Architecture

```
golf-dashboard/
├── backend/                        # FastAPI REST API
│   ├── main.py                     # App entry point + DB initialization
│   ├── database.py                 # SQLAlchemy setup + session factory
│   ├── auth.py                     # Password hashing + JWT token management
│   ├── models.py                   # SQLAlchemy ORM models (User, SwingSession)
│   ├── schemas.py                  # Pydantic request/response schemas
│   ├── job_store.py                # In-memory job state management
│   ├── requirements_api.txt        # API dependencies
│   └── routers/
│       ├── auth.py                 # POST /api/auth/{register,login}, GET/PATCH /api/auth/me
│       ├── analysis.py             # POST /api/analyze, GET /api/status, /api/report
│       ├── sessions.py             # GET /api/sessions/{list,dashboard}, DELETE /api/sessions/{id}
│       └── live.py                 # GET /api/live/frame (webcam)
├── frontend/                       # React + Vite + TailwindCSS
│   ├── package.json                # NPM dependencies
│   ├── vite.config.ts              # Vite bundler config
│   ├── tsconfig.json               # TypeScript config
│   └── src/
│       ├── App.tsx                 # Main router + protected routes
│       ├── main.tsx                # Vite entry point
│       ├── index.css               # Global styles
│       ├── api/
│       │   ├── client.ts           # Axios client with auth interceptor
│       │   ├── auth.ts             # Auth API endpoints
│       │   └── sessions.ts         # Sessions API endpoints
│       ├── store/
│       │   └── authStore.ts        # Zustand auth state (persisted to localStorage)
│       ├── pages/
│       │   ├── LoginPage.tsx       # User login form
│       │   ├── RegisterPage.tsx    # User registration form
│       │   ├── DashboardPage.tsx   # Swing history + charts
│       │   ├── ProfilePage.tsx     # Edit user profile
│       │   ├── AnalyzePage.tsx     # Video upload + analysis
│       │   └── LivePage.tsx        # Real-time webcam feedback
│       ├── components/
│       │   ├── auth/
│       │   │   └── ProtectedRoute.tsx  # Route guard for authenticated pages
│       │   ├── layout/
│       │   │   └── Navbar.tsx      # Auth-aware navigation bar
│       │   └── ...
│       └── hooks/                  # Custom React hooks
├── models/                         # Pre-trained ML models
│   ├── fault_detector.pt           # PyTorch fault classifier (~50MB)
│   ├── performance_predictor.pt    # Distance/speed predictor model
│   ├── ball_detector.pt            # YOLOv8 ball detector
│   ├── pose_landmarker_full.task   # MediaPipe pose landmarks model
│   └── swing_quality_classifier.pt # Swing quality classifier
├── utils/                          # Core ML & video processing
│   ├── video_processor.py          # Video I/O + annotated video generation
│   ├── pose_detector.py            # MediaPipe pose extraction
│   ├── phase_detector.py           # Swing phase classification (6 phases)
│   ├── ball_tracker.py             # YOLO ball tracking + filtering
│   ├── distance_estimator.py       # Ball distance estimation
│   ├── swing_phase_analyzer.py     # Phase-specific fault analysis
│   ├── feature_extractor.py        # ML feature extraction
│   └── visualizer.py               # Video annotation utilities
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
