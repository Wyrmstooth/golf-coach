# Golf Dashboard - Complete Deployment Guide with Colab Worker

## Overview

Your golf-dashboard now has **two deployment modes**:

- **Local Mode** (development): Analysis runs inside the web service (uses lots of RAM)
- **Remote Mode** (production): Analysis jobs queue in PostgreSQL, and an external worker (Colab/your machine) processes them

This guide shows you how to set up both your **production backend** and **Colab worker** to split the compute load.

---

## Part 1: Backend Setup (Fly.io or Render)

### Step 1: Generate Required Secrets

Open PowerShell and generate secure random strings:

```powershell
# Generate a SECRET_KEY (64 characters minimum)
-join ((33..126) | Get-Random -Count 64 | ForEach-Object {[char]$_})

# Generate ANALYSIS_WORKER_SECRET (at least 32 characters)
-join ((33..126) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

**Save these values** — you'll need them below.

---

### Step 2: Set Environment Variables on Your Hosting

#### **If using Render:**

Go to **Dashboard → golfcoach-backend → Environment**. Add or update:

| Key | Value | Notes |
|-----|-------|-------|
| `DATABASE_URL` | Your Neon PostgreSQL URL | `postgresql://user:password@host/dbname?sslmode=require` |
| `SECRET_KEY` | The 64-char secret from Step 1 | Used for JWT token signing |
| `ALLOWED_ORIGINS` | `https://golf-coach-frontend.onrender.com` | Frontend domain (adjust if different) |
| `ENVIRONMENT` | `production` | Enables remote mode by default |
| `ANALYSIS_EXECUTION_MODE` | `remote` | **Critical** — makes analysis queue instead of inline |
| `ANALYSIS_WORKER_SECRET` | The 32-char secret from Step 1 | Shared with Colab worker for auth |
| `PYTHONUNBUFFERED` | `1` | Ensures logs stream properly |
| `MPLBACKEND` | `Agg` | Non-GUI matplotlib backend |

#### **If using Fly.io:**

Update `fly.toml`:

```toml
[env]
  PYTHONUNBUFFERED = "1"
  MPLBACKEND = "Agg"
  ENVIRONMENT = "production"
  ANALYSIS_EXECUTION_MODE = "remote"
  ALLOWED_ORIGINS = "https://golf-coach-frontend.onrender.com"  # or your actual frontend URL
  ANALYSIS_WORKER_SECRET = "your-32-char-secret-here"
  SECRET_KEY = "your-64-char-secret-here"
```

Then redeploy:

```bash
flyctl deploy
```

---

### Step 3: Migrate the Database

Once the backend is running, the new `analysis_jobs` table will be created **automatically on first request** thanks to the self-healing job store. However, you can manually trigger it:

```bash
# SSH into Render backend or use flyctl
# Then run:
python -c "from backend.database import init_db; init_db()"
```

Or just upload a video from the frontend — that will trigger table creation.

---

### Step 4: Update Frontend API URL (if needed)

If your backend hostname changed from `golfcoach-backend.onrender.com` to something else:

**In `frontend/src/api/base.ts`:**

```typescript
export function getApiBase(): string {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  // ... fallback logic
}
```

**In `render.yaml` (frontend static site section):**

```yaml
buildEnvVars:
  - key: VITE_API_URL
    value: https://your-backend-url.onrender.com/api
```

Then redeploy the frontend.

---

## Part 2B: Finding Your Backend URL & Secret (Visual Guide)

### **Finding Your Backend URL**

1. Open [Render Dashboard](https://dashboard.render.com/)
2. Click **golfcoach-backend** service
3. Look at the top of the page — you'll see something like:
   ```
   https://golfcoach-backend-abc123.onrender.com
   ```
4. **Copy that whole URL** — that's your `BACKEND_URL`

### **Finding Your ANALYSIS_WORKER_SECRET**

1. In the same Render page, scroll down to **Environment**
2. Look for the row with key `ANALYSIS_WORKER_SECRET`
3. Click the **eye icon** to reveal the value
4. **Copy that value** — that's your `WORKER_SECRET` for Colab

**Example:**
- Backend URL: `https://golfcoach-backend-x9y2k.onrender.com`
- Worker Secret: `aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2u`

---

The Colab worker is a Python script that runs in Google Colab (free GPU + 12GB RAM) and continuously claims jobs from your queued backend, processes them, and uploads results.

### Step 1: Create a Colab Notebook and Install

1. Go to [Google Colab](https://colab.research.google.com)
2. Click **File** → **New Notebook**
3. Copy **entire block below** and paste into the first cell:

```python
# ============= INSTALL PACKAGES =============
!pip install -q requests sqlalchemy fastapi python-jose passlib[argon2] pillow opencv-python-headless

print("✅ Packages installed!")
```

4. Click ▶️ **Run** and wait 2 minutes

---

### Step 2: Set Configuration

Create a **second cell** and paste:

```python
import os

# ⬇️ CHANGE THESE TWO VALUES ⬇️
BACKEND_URL = "https://golf-dashboard-vmqd.onrender.com"  # Replace with YOUR backend URL
WORKER_SECRET = "-5&z2wvx*.>0QO]uE:cPaSd~gINk^M;X<"  # Replace with YOUR ANALYSIS_WORKER_SECRET

# Set environment variables
os.environ["BACKEND_URL"] = BACKEND_URL
os.environ["ANALYSIS_WORKER_SECRET"] = WORKER_SECRET
os.environ["WORKER_ID"] = "colab-worker-1"

print(f"✅ Configured!")
print(f"   Backend: {BACKEND_URL}")
print(f"   Secret: {WORKER_SECRET[:10]}...")
```

**Where to find these values:**

1. Open [Render Dashboard](https://dashboard.render.com/)
2. Click **golfcoach-backend**
3. Copy the URL from the top (your `BACKEND_URL`)
4. Scroll to **Environment** → find `ANALYSIS_WORKER_SECRET` → click eye icon → copy value

| What to Find | Example |
|---|---|
| **Backend URL** | `https://golfcoach-backend-abc123.onrender.com` |
| **ANALYSIS_WORKER_SECRET** | `aBcD1234eFgH5678ijKl9012mnOp` |

5. Paste both values into the cell above, then click ▶️ **Run**

---

### Step 3: Upload the Analyzer Files (Private Repo)

**⚠️ Your repo is private, so we'll upload files directly instead of downloading from GitHub.**

1. In your local repo, zip up the **core files** you need:
   - `analyze_video.py`
   - `pose_detector.py`
   - `config.yaml`
   - Entire `utils/` folder
   - Entire `models/` folder (includes `.pt` weight files)

2. **Upload to Colab:**
   - Click the **folder icon** (left sidebar)
   - Click the **upload file icon** (looks like ⬆️)
   - Select your zip file
   - Wait for upload to complete

3. **Extract in Colab** - create a **third cell** and paste:

```python
import shutil
import os

# Extract uploaded zip
if os.path.exists("golf-files.zip"):
    shutil.unpack_archive("golf-files.zip", "/tmp/golf")
    os.chdir("/tmp/golf")
    print("✅ Files extracted to /tmp/golf")
else:
    print("❌ Upload golf-files.zip first!")
```

Click ▶️ **Run**

---

### Step 4: Start the Remote Worker

Create a **fourth cell** and paste the complete worker (this is the main worker loop):

```python
import os
import requests
import json
from pathlib import Path
import time
import sys

# Make sure we're in the right directory
os.chdir("/tmp/golf")
sys.path.insert(0, "/tmp/golf")

# Get config
backend_url = os.environ.get("BACKEND_URL")
secret = os.environ.get("ANALYSIS_WORKER_SECRET")
worker_id = os.environ.get("WORKER_ID", "colab-worker-1")

if not backend_url or not secret:
    print("❌ ERROR: Set BACKEND_URL and ANALYSIS_WORKER_SECRET in Step 2 first!")
    sys.exit(1)

print(f"🎯 Worker Starting...")
print(f"   Backend: {backend_url}")
print(f"   Worker ID: {worker_id}")
print(f"   Polling every 10 seconds for jobs...\n")

# ============= HELPER FUNCTIONS =============

def claim_job():
    """Claim the next available job from the backend"""
    try:
        response = requests.post(
            f"{backend_url}/api/worker/jobs/next",
            headers={"X-Worker-Secret": secret},
            timeout=10
        )
        if response.status_code == 200:
            job = response.json()
            if job and job.get("job_id"):
                return job
        elif response.status_code == 204:
            return None  # No jobs available
        return None
    except Exception as e:
        return None

def download_video(job_id, output_path):
    """Download the video for a job"""
    try:
        response = requests.get(
            f"{backend_url}/api/worker/jobs/{job_id}/download",
            headers={"X-Worker-Secret": secret},
            stream=True,
            timeout=120
        )
        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            with open(output_path, "wb") as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            pct = int((downloaded / total_size) * 20)  # 0-20% for download
                            send_progress(job_id, pct)
            return True
        return False
    except Exception as e:
        return False

def send_progress(job_id, progress_percent):
    """Update job progress on backend"""
    try:
        requests.post(
            f"{backend_url}/api/worker/jobs/{job_id}/progress",
            headers={"X-Worker-Secret": secret},
            json={"progress": min(progress_percent, 99)},  # Never 100% until complete
            timeout=10
        )
    except:
        pass

def upload_results(job_id, report_json, output_dir):
    """Upload analysis results back to backend"""
    try:
        # Build files dict
        files_dict = {}
        
        # Add report.json
        files_dict["report"] = ("report.json", json.dumps(report_json))
        
        # Add output files
        if Path(output_dir).exists():
            for file_path in Path(output_dir).glob("*"):
                if file_path.is_file():
                    with open(file_path, "rb") as f:
                        files_dict[file_path.name] = (file_path.name, f.read())
        
        response = requests.post(
            f"{backend_url}/api/worker/jobs/{job_id}/complete",
            headers={"X-Worker-Secret": secret},
            files=files_dict,
            timeout=120
        )
        return response.status_code == 200
    except Exception as e:
        return False

def analyze_video_real(video_path, job_id, output_dir):
    """Run the REAL analyzer using MLSwingAnalyzer"""
    try:
        # Import the analyzer
        from analyze_video import MLSwingAnalyzer
        
        send_progress(job_id, 25)
        
        # Create output dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Run analysis
        analyzer = MLSwingAnalyzer()
        send_progress(job_id, 30)
        
        report = analyzer.analyze_video(video_path, output_dir)
        send_progress(job_id, 95)
        
        return report
    except Exception as e:
        print(f"      ❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()
        return None

# ============= MAIN WORKER LOOP =============

empty_count = 0
while True:
    job = claim_job()
    
    if job and job.get("job_id"):
        empty_count = 0
        job_id = job.get("job_id")
        video_path = f"/tmp/job_{job_id}.mp4"
        output_dir = f"/tmp/output_{job_id}"
        
        print(f"✅ Job claimed: {job_id}")
        send_progress(job_id, 1)
        
        # Download
        print(f"   📥 Downloading video...")
        if not download_video(job_id, video_path):
            print(f"   ❌ Failed to download")
            try:
                requests.post(f"{backend_url}/api/worker/jobs/{job_id}/fail",
                             headers={"X-Worker-Secret": secret},
                             json={"error": "Failed to download video"})
            except:
                pass
            continue
        
        # Analyze
        print(f"   🔍 Running analysis...")
        result = analyze_video_real(video_path, job_id, output_dir)
        
        if result is None:
            print(f"   ❌ Analysis failed")
            try:
                requests.post(f"{backend_url}/api/worker/jobs/{job_id}/fail",
                             headers={"X-Worker-Secret": secret},
                             json={"error": "Analysis failed"})
            except:
                pass
            continue
        
        # Upload
        print(f"   📤 Uploading results...")
        if upload_results(job_id, result, output_dir):
            print(f"   ✅ Complete!\n")
        else:
            print(f"   ❌ Upload failed\n")
    else:
        empty_count += 1
        if empty_count == 1:
            print("⏳ Waiting for jobs... (polling every 10s)")
        time.sleep(10)
```

Click ▶️ **Run** and the worker will start polling

**Output should look like:**
```
🎯 Worker Starting...
   Backend: https://golfcoach-backend.onrender.com
   Worker ID: colab-worker-1
   Polling every 10 seconds for jobs...

⏳ Waiting for jobs... (polling every 10s)
```

**Leave this cell running!** It will continuously check for jobs.

### Step 4: Keep Colab Running (Optional - Prevents Disconnects)

**Important:** Colab disconnects after 30 minutes of inactivity. To keep it running:

1. Create a **fourth cell** with this keep-alive code:

```python
from IPython.display import clear_output
import time

def keep_alive_loop():
    start_time = time.time()
    while True:
        clear_output(wait=True)
        elapsed = int(time.time() - start_time)
        hours = elapsed // 3600
        mins = (elapsed % 3600) // 60
        print(f"🟢 Colab connected | Uptime: {hours}h {mins}m")
        time.sleep(60)

keep_alive_loop()
```

2. Click ▶️ **Run** — this will display connection status and keep Colab alive

**Alternative:** Run Colab on a persistent machine (AWS EC2 free tier, Fly.io, local desktop, etc.)

---

## Part 3: Complete Flow Test (Verify Everything Works)

### Step 1: Verify Backend is Running

```bash
curl https://your-backend-url/api/health
```

Expected response:

```json
{
  "status": "ok",
  "version": "2.0.0",
  "active_jobs": 0,
  "total_jobs": 0
}
```

### Step 2: Login to Frontend

1. Go to `https://golf-coach-frontend.onrender.com` (or your frontend URL)
2. **Register** a new account or **Login**
3. Navigate to **Analyze** (now requires login)

### Step 3: Upload a Video

1. Drop a golf swing video (MP4, MOV, AVI, MKV)
2. Click **Analyze My Swing**
3. You should see **"Pending..."** (queued state) instead of immediate analysis

### Step 4: Start Colab Worker

If not already running, go back to your Colab notebook and make sure **Step 3** (the worker loop) is running.

### Step 5: Watch the Magic

1. Refresh the frontend page every few seconds
2. The progress should move: `Pending` → `Running (5%)` → `Running (25%)` → ... → `Done (100%)`
3. Results appear automatically once the Colab worker finishes

---

## Part 5: Environment Variables Reference

### Backend (set on Render/Fly.io)

| Variable | Example | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection string |
| `SECRET_KEY` | 64+ random chars | JWT signing key |
| `ALLOWED_ORIGINS` | `https://golf-coach-frontend.onrender.com` | CORS allowed frontend domain |
| `ENVIRONMENT` | `production` | Dev/prod mode |
| `ANALYSIS_EXECUTION_MODE` | `remote` | Queue jobs (remote) or run inline (local) |
| `ANALYSIS_WORKER_SECRET` | 32+ random chars | Shared secret for worker authentication |
| `PORT` | `8080` | (Render/Fly.io sets this automatically) |

### Colab/Local Worker (set in notebook or `.env`)

| Variable | Example | Purpose |
|----------|---------|---------|
| `BACKEND_URL` | `https://golfcoach-backend.onrender.com` | Your backend hostname |
| `ANALYSIS_WORKER_SECRET` | Same as backend | Must match backend secret |
| `WORKER_ID` | `colab-worker-1` | Identifier for this worker instance |
| `WORKER_POLL_INTERVAL` | `10` | Seconds between job checks |

---

## Part 6: Troubleshooting

### Problem: "404: Not Found" when running Colab cell

**Cause:** Old setup tried downloading from GitHub and failed (network issue or auth).

**Fix:** Use the new inline setup (Step 1-3 above) which doesn't require downloading from GitHub. All code is pasted directly into Colab.

---

### Problem: "Analysis stuck at Pending"

**Cause:** Colab worker isn't running or can't reach the backend.

**Fix:**
1. Check Colab is still running (not disconnected)
2. Verify `BACKEND_URL` is correct (no typos, HTTPS only)
3. Check `ANALYSIS_WORKER_SECRET` matches on both sides
4. Look at Colab logs for error messages

### Problem: "401 Unauthorized" in Colab logs

**Cause:** Worker secret mismatch.

**Fix:**
1. Copy the exact secret from backend env vars
2. Paste into Colab notebook
3. No extra spaces or quotes

### Problem: "Job not found" (404)

**Cause:** Backend restart lost in-memory job state (old system). Now all jobs are in PostgreSQL, so they should persist.

**Fix:**
1. Verify `DATABASE_URL` is set correctly on backend
2. Check backend logs: `SELECT * FROM analysis_jobs;` in your database

### Problem: Colab runs out of memory

**Cause:** Video is too large or MediaPipe models are heavy.

**Fix:**
1. Reduce video resolution before uploading
2. Use shorter videos (< 30 seconds)
3. Run Colab with GPU enabled (Runtime → Change Runtime Type → GPU)

### Problem: "ANALYSIS_WORKER_SECRET is not configured"

**Cause:** Backend doesn't have the env var set.

**Fix:**
1. On Render: add it to environment variables
2. On Fly.io: add to `fly.toml` and redeploy
3. Restart the backend service

---

## Part 7: Production Checklist

- [ ] Backend env vars set (see Part 1, Step 2)
- [ ] Database URL points to working PostgreSQL (Neon or Render managed)
- [ ] `ANALYSIS_EXECUTION_MODE=remote` on backend
- [ ] `ANALYSIS_WORKER_SECRET` generated and set on both backend + Colab
- [ ] Frontend can access backend (CORS, domain, HTTPS)
- [ ] Colab worker notebook created and tested
- [ ] At least one test upload → analysis → result flow completed
- [ ] Colab connected to internet and not running other heavy tasks
- [ ] Backend logs accessible (Render: Logs tab, Fly.io: `flyctl logs`)

---

## Part 8: Advanced: Running Worker Locally (Alternative to Colab)

If you want to run the worker on your own machine instead of Colab:

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r backend/requirements_api.txt

# Set env vars (Windows PowerShell)
$env:BACKEND_URL = "https://your-backend-url"
$env:ANALYSIS_WORKER_SECRET = "your-secret"
$env:WORKER_ID = "local-worker-1"

# Run worker
python colab_worker.py
```

The script is identical whether running in Colab, locally, or on a cloud VM — it just needs internet access to your backend.

---

## Part 9: Scaling Beyond One Worker

If one Colab worker is too slow:

1. Start **multiple Colab notebooks** with different `WORKER_ID` values
2. They'll automatically claim different jobs from the queue
3. Jobs process in parallel across all workers
4. Results stream back independently

Example: 3 workers all running `python colab_worker.py` will process 3 videos simultaneously.

---

## Support

If something breaks:

1. **Check backend logs** (Render → Logs or `flyctl logs`)
2. **Check Colab output** (scroll up in notebook)
3. **Verify env vars** match exactly (case-sensitive, no extra spaces)
4. **Test endpoints manually:**

```bash
# Check backend health
curl https://your-backend-url/api/health

# List all jobs (replace with your URL)
curl -X GET https://your-backend-url/api/history
```

---

**You're all set!** Your golf-dashboard now uses Colab's free GPU to handle heavy video analysis while keeping your backend lightweight.
