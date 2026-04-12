# 🏌️ GolfCoach AI - Complete Setup & Running Instructions

## ✅ What's Been Done

### 1. **Miniconda Installed**
   - Downloaded and installed Miniconda for Windows
   - Accepted all license terms

### 2. **Python 3.10 Environment Created**
   - Created conda environment `golfpose` with Python 3.10
   - Required because MediaPipe Tasks API is broken on Python 3.13+

### 3. **Dependencies Installed**
   - Machine Learning: `mediapipe` 0.10.33, `opencv-python`, `numpy`, `scipy`, `matplotlib`, `pytorch`, `ultralytics`
   - Backend API: `fastapi`, `uvicorn`, `python-multipart`, `websockets`, `aiofiles`
   - Frontend: React 19, TypeScript 5.9, Vite 8, Tailwind CSS, Recharts, Zustand

### 4. **MediaPipe Compatibility Shim Created**
   - **Problem:** MediaPipe 0.10.x removed `mp.solutions` module
   - **Solution:** Created `mediapipe_compat.py` that patches `mp.solutions` back using the Tasks API
   - **Model:** Downloaded `pose_landmarker_full.task` (~9MB) to `models/` folder
   - All existing code that does `import mediapipe as mp; mp.solutions.pose` works unchanged

### 5. **Services Configured**
   - ✅ Frontend runs on **http://localhost:5173** (Vite dev server)
   - ✅ Backend runs on **http://localhost:8000** (FastAPI with WebSocket support)
   - ✅ API docs available at **http://localhost:8000/docs**

---

## 🚀 How to Run Everything

### **OPTION A: Automatic (Recommended)**

Open two PowerShell terminals:

**Terminal 1 – Backend:**
```powershell
cd C:\Users\umer_\OneDrive\Desktop\golf-dashboard
powershell -ExecutionPolicy Bypass -File start_backend.ps1
```

**Terminal 2 – Frontend:**
```powershell
cd C:\Users\umer_\OneDrive\Desktop\golf-dashboard\frontend
npm run dev
```

Then open your browser and go to: **http://localhost:5173**

---

### **OPTION B: Manual Step-by-Step**

#### **Step 1: Start the Backend (Python FastAPI)**

Open PowerShell and run:
```powershell
cd C:\Users\umer_\OneDrive\Desktop\golf-dashboard

# IMPORTANT: Always use the golfpose Python directly
& "$env:USERPROFILE\miniconda3\envs\golfpose\python.exe" -m uvicorn backend.main:app --reload --port 8000
```

Expected output:
```
INFO:     Will watch for changes in these directories: ['C:\Users\umer_\OneDrive\Desktop\golf-dashboard']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX] using WatchFiles
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

✅ **Backend is ready** → http://localhost:8000

#### **Step 2: Start the Frontend (Node/Vite)**

Open a **second PowerShell** and run:
```powershell
cd C:\Users\umer_\OneDrive\Desktop\golf-dashboard\frontend
npm run dev
```

Expected output:
```
VITE v8.0.0  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

✅ **Frontend is ready** → http://localhost:5173

#### **Step 3: Open the App**

Open your browser:
```
http://localhost:5173
```

You should see the **GolfCoach AI Dashboard** with three modes:
- 📹 **Video Analysis** — Upload a golf swing video for analysis
- 🎥 **Live ADDRESS Pose Check** — Real-time posture correction via webcam
- 🏌️ **Live Swing Analysis** — Real-time swing phase detection

---

## ⚠️ CRITICAL: Python Version Issue

### **The Problem**
- Base conda environment uses **Python 3.13**
- MediaPipe Tasks API doesn't work on Python 3.13
- Will crash with: `AttributeError: function 'free' not found`

### **The Solution**
Always start the backend with the **golfpose Python 3.10**:

✅ **CORRECT:**
```powershell
& "$env:USERPROFILE\miniconda3\envs\golfpose\python.exe" -m uvicorn backend.main:app --reload --port 8000
```

❌ **WRONG (will crash):**
```powershell
uvicorn backend.main:app --reload --port 8000
python -m uvicorn backend.main:app --reload --port 8000
conda activate golfpose; uvicorn ...  # May pick up wrong Python
```

**Use the script provided:**
```powershell
powershell -ExecutionPolicy Bypass -File start_backend.ps1
```

---

## 📂 Project Structure

```
golf-dashboard/
├── frontend/                    # React + TypeScript + Vite
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api/                 # API clients
│   │   ├── components/          # React components
│   │   ├── pages/               # Page components
│   │   └── store/               # Zustand state
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                     # FastAPI server
│   ├── main.py                  # FastAPI app + CORS
│   ├── routers/
│   │   ├── analysis.py          # Video analysis endpoint
│   │   └── live.py              # WebSocket live modes
│   ├── job_store.py             # Job tracking
│   └── requirements_api.txt
│
├── models/                      # Pre-trained models
│   ├── pose_landmarker_full.task  # MediaPipe model
│   ├── fault_detector.pt        # PyTorch fault detection
│   └── performance_predictor.pt # PyTorch performance prediction
│
├── utils/                       # Python utilities
│   ├── pose_detector.py         # MediaPipe pose detection
│   ├── biomechanics.py          # Angle calculations
│   ├── swing_phase_analyzer.py  # Phase detection
│   ├── trajectory_extractor.py  # Landmark tracking
│   ├── ball_tracker.py          # Ball trajectory
│   ├── distance_estimator.py    # Distance estimation
│   ├── video_processor.py       # Video processing
│   └── visualizer.py            # Plotting
│
├── mediapipe_compat.py          # ⭐ Compatibility shim
├── pose_detector.py             # Pose detection wrapper
├── analyze_video.py             # Main analysis pipeline
├── phase_detector.py            # Phase detection
├── golf_coach_app.py            # Streamlit app
├── config.yaml                  # Configuration
├── requirements.txt             # Python dependencies
├── start_backend.ps1            # ⭐ Backend launcher
├── start_app.ps1                # All-in-one launcher
└── README.md
```

---

## 🔧 Key Files to Know

| File | Purpose |
|------|---------|
| `start_backend.ps1` | ⭐ **Use this to start the backend** |
| `mediapipe_compat.py` | Patches `mp.solutions` for MediaPipe 0.10.x |
| `backend/main.py` | FastAPI app with CORS config |
| `backend/routers/analysis.py` | Video analysis endpoints |
| `backend/routers/live.py` | WebSocket live endpoints |
| `frontend/src/api/analysis.ts` | Frontend API calls |
| `config.yaml` | ML model parameters |

---

## 📱 Frontend Usage

### **1. Video Analysis**
1. Click "📹 Video Analysis"
2. Upload an MP4, MOV, or AVI golf swing video
3. Click "🚀 Analyze Swing"
4. Wait for analysis (takes 1-5 minutes depending on video length)
5. View results: phases, faults, performance predictions, annotated video

### **2. Live ADDRESS Pose Check**
1. Click "🎥 Live ADDRESS Pose Check"
2. Click "▶️ Start Camera"
3. Allow camera access
4. Adjust your posture based on real-time feedback
5. Target metrics shown on right:
   - Spine Angle: 150-165°
   - Left/Right Knee: 140-160°
   - Left Arm: >150°

### **3. Live Swing Analysis**
1. Click "🏌️ Live Swing Analysis"
2. Record swing phases in real-time
3. See which phase you're in (ADDRESS → BACKSWING → TOP → DOWNSWING → IMPACT → FOLLOW-THROUGH)

---

## 🐛 Troubleshooting

### **Backend won't start / "Analysis Failed" error**
✅ **FIX:** Always use this command:
```powershell
& "$env:USERPROFILE\miniconda3\envs\golfpose\python.exe" -m uvicorn backend.main:app --reload --port 8000
```

Or use the script:
```powershell
powershell -ExecutionPolicy Bypass -File start_backend.ps1
```

### **Frontend shows "Network Error" / Cannot connect to backend**
1. Check backend is running on http://localhost:8000
2. Verify CORS is enabled (check `backend/main.py` line ~30)
3. Both servers must be running:
   - Backend on :8000
   - Frontend on :5173

### **Camera not working in Live modes**
- Allow camera permissions when browser asks
- Check Windows Settings → Privacy & Security → Camera
- Close other apps using camera

### **Video analysis times out**
- Video is too long or too large
- Use MP4 format (best supported)
- Try a shorter clip (< 2 minutes)

### **Missing model errors**
```
FileNotFoundError: ... pose_landmarker_full.task
```
Download it manually:
```powershell
$url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task"
$dest = "C:\Users\umer_\OneDrive\Desktop\golf-dashboard\models\pose_landmarker_full.task"
Invoke-WebRequest -Uri $url -OutFile $dest
```

---

## 📊 API Endpoints

### **Analysis Endpoints**
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/analyze` | Upload video for analysis |
| GET | `/api/status/{job_id}` | Check job status |
| GET | `/api/report/{job_id}` | Get analysis results |
| GET | `/api/files/{job_id}/{filename}` | Download output files |

### **Live Endpoints**
| Protocol | Endpoint | Purpose |
|----------|----------|---------|
| WS | `/api/live/address` | Real-time ADDRESS pose feedback |
| POST | `/api/live/swing` | Upload recorded swing video |

### **API Documentation**
Open: **http://localhost:8000/docs** (Swagger UI)

---

## 🎯 Quick Start Checklist

- [ ] Backend running: `powershell -ExecutionPolicy Bypass -File start_backend.ps1`
- [ ] Frontend running: `cd frontend && npm run dev`
- [ ] Browser open: http://localhost:5173
- [ ] API docs available: http://localhost:8000/docs
- [ ] Upload a golf swing video
- [ ] Check analysis results

---

## 📝 Notes

- **Warnings about `inference_feedback_manager`** are harmless — MediaPipe internal messages
- **Video processing is CPU-intensive** — analysis takes several minutes
- **First run is slower** due to model loading
- **CORS is configured** to allow localhost:5173 to call localhost:8000
- **Jobs are tracked in memory** — restart clears job history

---

## 🆘 Need Help?

1. **Check backend is running with golfpose Python** — use `start_backend.ps1`
2. **Check both ports are open** — :8000 and :5173
3. **Verify model file exists** — `models/pose_landmarker_full.task`
4. **Check logs in backend terminal** for error details
5. **Test API directly** → http://localhost:8000/docs (Swagger)
