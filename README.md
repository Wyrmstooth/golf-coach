# 🏌️ GolfCoach AI — AI-Powered Golf Swing Analyzer

**Professional golf swing analysis using MediaPipe pose estimation, ML fault detection, ball tracking, and performance prediction — served via a modern React + FastAPI web app.**

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![React](https://img.shields.io/badge/React-19-61dafb.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.21-green.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)

---

## 🎯 Features

- **6-Phase Swing Detection** — ADDRESS → BACKSWING → TOP → DOWNSWING → IMPACT → FOLLOW-THROUGH
- **ML Fault Detection** — 92% accuracy PyTorch classifier with per-phase severity ratings (🔴🟠🟡)
- **Performance Prediction** — Neural network estimating ball speed, distance & carry (R²=0.67)
- **Ball Tracking (Module 3)** — YOLOv8 ball detection + trajectory + distance estimation
- **Annotated Video** — Pose skeleton overlay, phase labels, fault highlights, slow-motion
- **PDF Reports** — Downloadable multi-page analysis with per-phase fault tables
- **Live Webcam** — Real-time ADDRESS pose checking before you swing
- **Golf-Themed UI** — Animated loading, ball trajectory chart with projection line

---

## 🗂️ Architecture

```
golf_optimized/
├── backend/                   # FastAPI backend
│   ├── main.py                # App entry point
│   ├── job_store.py           # In-memory job state
│   └── routers/
│       ├── analysis.py        # POST /api/analyze, GET /api/status, /api/report
│       └── live.py            # GET /api/live/frame (webcam)
├── frontend/                  # React + Vite + TailwindCSS
│   └── src/
│       ├── pages/             # LandingPage, AnalyzePage, LivePage
│       ├── components/        # UI components (upload, results, layout)
│       ├── hooks/             # useAnalysisJob (polling hook)
│       ├── api/               # Axios API client
│       └── store/             # Zustand state store
├── analyze_video.py           # Core ML analysis (MLSwingAnalyzer)
├── utils/
│   ├── video_processor.py     # Video I/O + annotated video generation
│   ├── ball_tracker.py        # Ball tracking pipeline
│   ├── distance_estimator.py  # Ball distance estimation
│   └── ...
├── models/
│   ├── fault_detector.pt      # PyTorch fault classifier
│   ├── performance_predictor.pt # Distance/speed predictor
│   └── ball_detector.pt       # YOLOv8 ball detector
├── config.yaml                # Runtime configuration
├── requirements.txt           # Python dependencies
├── start_app.ps1              # One-click Windows launcher
└── SETUP_WINDOWS.md           # Detailed Windows setup guide
```

---

## 🚀 Quick Start

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.9 – 3.11 | Backend & ML |
| Conda / Miniconda | Any | Environment management |
| Node.js | 18+ | Frontend build |
| npm | 9+ | Frontend packages |

> **Windows users** → see **[SETUP_WINDOWS.md](SETUP_WINDOWS.md)** for the full guide.  
> **Linux users** → see **[SETUP_LINUX.md](SETUP_LINUX.md)** for the full guide.

---

### Windows — One-click launch

```powershell
# From the golf_optimized/ directory
powershell -ExecutionPolicy Bypass -File start_app.ps1
```

This automatically starts the FastAPI backend (port 8000) and the React dev server (port 5173).

---

### Manual start (Windows & Linux)

**Terminal 1 — Python backend:**

```bash
conda activate golfpose
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — React frontend:**

```bash
cd frontend
npm install      # first time only
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/zainulabidin776/golf-dashboard.git
cd golf-dashboard
```

### 2. Create the Python environment

```bash
conda create -n golfpose python=3.10 -y
conda activate golfpose
pip install -r requirements.txt
```

### 3. Verify MediaPipe

```bash
python -c "import mediapipe as mp; print(mp.__version__); print(hasattr(mp, 'solutions'))"
# Expected: 0.10.21 / True
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. (Optional) Train ML models

Pre-trained models (`fault_detector.pt`, `performance_predictor.pt`) are included. Re-train only if you have new data:

```bash
python training/train_pytorch_models.py
```

---

## 🌐 Using the Web App

1. Open **http://localhost:5173**
2. Go to **Analyze** tab
3. Drag & drop a golf swing video (MP4, MOV, AVI — max 500 MB)
4. Click **Analyze My Swing**
5. Watch live progress (pose → phases → faults → performance → ball tracking → report)
6. View results: swing score, fault cards, trajectory chart, performance metrics
7. Click **Download Full Report** for a PDF with all details

---

## 📊 Output

| File | Description |
|------|-------------|
| `*_report.json` | Complete analysis: phases, faults, performance, ball tracking |
| `*_analysis.png` | Wrist trajectory plot with phase markers |
| `*_annotated.mp4` | 50%-speed video with pose overlay + fault labels |
| `*_ball_traj.csv` | Per-frame ball coordinates and confidence |

---

## 🛠️ Configuration

Edit `config.yaml` to tune behaviour:

```yaml
# Ball tracking (Module 3)
module3:
  enabled: true
  ball_detection:
    model_path: models/ball_detector.pt
    conf_threshold: 0.4
  ball_tracking:
    window_after_impact: 70   # frames to track after impact
```

---

## 🧪 Troubleshooting

| Error | Fix |
|-------|-----|
| `module 'mediapipe' has no attribute 'solutions'` | Activate `golfpose` env; ensure `mediapipe==0.10.21` |
| `ModuleNotFoundError` on startup | `pip install -r requirements.txt` |
| Backend won't start — sklearn/cv2 error | Only `fastapi` & `uvicorn` needed at startup; ML deps load at analysis time |
| Analysis stuck at 88% | Upgrade OpenCV or apply the mp4v codec fix (already in `video_processor.py`) |
| `OSError: [WinError 6] The handle is invalid` | Already fixed — `_safe_tqdm()` handles invalid stderr handles in uvicorn threads |
| Ball tracking shows "Not Available" | Place `ball_detector.pt` in `models/` directory |

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
