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

### Step 1: Create a Colab Notebook

1. Go to [Google Colab](https://colab.research.google.com)
2. Click **File** → **New Notebook**
3. Copy **entire block below** and paste into the first cell:

```python
# ============= GOLF DASHBOARD COLAB WORKER =============
# Just run this cell — it handles everything

# Step 1: Install packages (takes ~2 min)
!pip install -q requests sqlalchemy fastapi python-jose passlib[argon2]

# Step 2: Download the worker script directly
import requests
url = "https://raw.githubusercontent.com/zainulabidin776/golf-dashboard/master/colab_worker.py"
response = requests.get(url)
with open("colab_worker.py", "w") as f:
    f.write(response.text)

# Step 3: Download analyze_video.py and supporting files
url2 = "https://raw.githubusercontent.com/zainulabidin776/golf-dashboard/master/analyze_video.py"
response2 = requests.get(url2)
with open("analyze_video.py", "w") as f:
    f.write(response2.text)

print("✅ Files downloaded!")

# Step 4: Set your configuration (FILL IN THE VALUES BELOW)
import os

BACKEND_URL = "https://golfcoach-backend.onrender.com"  # ← CHANGE THIS to your backend URL
WORKER_SECRET = "your-32-char-secret-here"              # ← CHANGE THIS to your ANALYSIS_WORKER_SECRET

# Set environment
os.environ["BACKEND_URL"] = BACKEND_URL
os.environ["ANALYSIS_WORKER_SECRET"] = WORKER_SECRET
os.environ["WORKER_ID"] = "colab-worker-1"

print(f"✅ Configured to use: {BACKEND_URL}")
print("✅ Ready to start worker!")
```

### **Fill in these TWO values:**

Find them on your **Render backend** (Dashboard → golfcoach-backend → Environment):

| What to Find | Where to Get It | Example |
|---|---|---|
| **Backend URL** | Render dashboard top shows the URL | `https://golfcoach-backend.onrender.com` |
| **ANALYSIS_WORKER_SECRET** | Environment Variables list | `aBcD1234eFgH5678ijKl9012mnOp` |

**Paste the values into the code above, then click the ▶️ Run button**

### Step 2: Start the Worker

1. **Scroll down** and create a **second cell** (Insert → Code)
2. Copy-paste this:

```python
# ============= START THE WORKER =============
# This will run forever, checking for jobs every 10 seconds
# It's safe to leave running — it just polls and waits

import time
import requests
import json
from pathlib import Path

# Verify config worked
backend_url = os.environ.get("BACKEND_URL")
secret = os.environ.get("ANALYSIS_WORKER_SECRET")

if not backend_url or not secret:
    print("❌ ERROR: Set BACKEND_URL and ANALYSIS_WORKER_SECRET in the first cell!")
    exit(1)

print(f"🎯 Worker starting...")
print(f"   Backend: {backend_url}")
print(f"   Checking for jobs every 10 seconds...")
print()

# Run the worker
exec(open("colab_worker.py").read())
```

3. Click the ▶️ **Run button**

The worker will start and show:
```
🎯 Worker starting...
   Backend: https://golfcoach-backend.onrender.com
   Checking for jobs every 10 seconds...

Waiting for jobs... (checks every 10s)
```

**Leave this cell running** — it will wait for jobs from your app.

### Step 3: Keep Colab Running

**Important:** Colab will disconnect if idle for >30 mins. To keep it running:

1. Add a keep-alive cell at the top:

```python
from IPython.display import clear_output
import time

def keep_alive():
    while True:
        clear_output(wait=True)
        print(f"Worker is alive: {time.strftime('%H:%M:%S')}")
        time.sleep(60)

# Run in background (optional)
import threading
threading.Thread(target=keep_alive, daemon=True).start()
```

2. Or run Colab on a persistent machine instead (AWS EC2, Fly.io, etc.)

---

## Part 3: Complete Flow Test

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

If not already running, start the Colab notebook (Part 2, Step 2 above).

### Step 5: Watch the Magic

1. Refresh the frontend page every few seconds
2. The progress should move: `Pending` → `Running (5%)` → `Running (25%)` → ... → `Done (100%)`
3. Results appear automatically once the Colab worker finishes

---

## Part 4: Environment Variables Reference

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

## Part 5: Troubleshooting

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

## Part 6: Production Checklist

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

## Part 7: Advanced: Running Worker Locally (Alternative to Colab)

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

## Part 8: Scaling Beyond One Worker

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
