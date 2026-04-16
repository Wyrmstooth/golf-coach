# 🔧 Deployment Troubleshooting — Fixes for Render Errors

## Current Error You're Seeing

```
ERROR: Could not find a version that satisfies the requirement mediapipe==0.10.21
ERROR: No matching distribution found for mediapipe==0.10.21
```

**Root Cause:** Your `requirements.txt` has `mediapipe==0.10.21` which is outdated (only 0.10.30-0.10.33 exist now)

---

## ✅ Quick Fix

### Step 1: Update Requirements
I've already fixed your requirements:
```
mediapipe==0.10.33  ← Changed from 0.10.21
```

### Step 2: Lock Python Version
I created `runtime.txt`:
```
python-3.10.15
```
This prevents Render from using Python 3.14.3 (which MediaPipe doesn't support)

### Step 3: Push Changes
```bash
git add .
git commit -m "Fix: Update MediaPipe to 0.10.33 and lock Python 3.10"
git push origin main
```

### Step 4: Redeploy on Render
1. Go to your **backend service** on Render dashboard
2. Click **"Manual Deploy"** → **"Deploy latest commit"**
3. Wait 5-10 minutes for rebuild

---

## 📋 What to Check in Render Set Up

### Backend Service Build Command
Should be:
```
pip install --no-cache-dir -r requirements.txt -r backend/requirements_api.txt
```

### Start Command
Should be:
```
python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

### Environment Variables (Must Have)
| Variable | Value |
|----------|-------|
| `PYTHONUNBUFFERED` | `1` |
| `MPLBACKEND` | `Agg` |
| `DATABASE_URL` | `postgresql://...` ← from your database |
| `ENVIRONMENT` | `production` |

---

## 🐍 Other Dependency Issues

### If You See "ImportError: No module named torch"
Your `requirements.txt` specifies PyTorch CPU version:
```
torch>=2.0.0,<2.2.0
torchvision>=0.15.0,<0.17.0
```

This is correct. If install fails on Render:
- **Solution:** Use Render's native Python 3.10 (already fixed by `runtime.txt`)

### If MediaPipe Still Fails to Import
- Make sure you're using Python 3.10, not 3.11+ 
- `runtime.txt` should force 3.10.15
- If still failing, check Render **Logs** → scroll to build section

---

## 📖 Render Deployment Files Reference

### Files Created:
- **`runtime.txt`** — Locks Python to 3.10.15
- **`requirements.txt`** — Updated MediaPipe to 0.10.33
- **`backend/requirements_api.txt`** — Added PostgreSQL driver
- **`backend/database.py`** — Updated for PostgreSQL support
- **`backend/main.py`** — Updated for environment variables

### You Don't Need:
- ❌ `Dockerfile` — Render doesn't use Docker for Python services
- ❌ `.dockerignore` — Only needed if using Docker
- ❌ `render.yaml` — Only needed for multi-service setups

---

## 🔄 Next Steps After Push

1. **Render auto-detects** your push
2. **Rebuilds backend** (~5-10 min)
3. **Frontend redeploys** automatically (~3-5 min)
4. **Your app is live** 🎉

You can watch progress in **Render Dashboard → Logs**

---

## 🆘 Still Failing?

### Check the Logs:
1. Render Dashboard → Your Backend Service
2. **"Logs"** tab → scroll down to build section
3. Look for the exact error message

### Common Causes:
- `DATABASE_URL` not set or wrong format
- `ALLOWED_ORIGINS` doesn't include frontend URL
- Build command missing one of the requirements files
- Python version not 3.10

### Quick Debug Step:
```bash
# Test locally first
python -m pip install -r requirements.txt -r backend/requirements_api.txt
python -m uvicorn backend.main:app
```

If this works locally, same build command works on Render.

---

## 📚 Documentation

- [Render Python Deployment](https://render.com/docs/python-version)
- [MediaPipe Requirements](https://ai.google.dev/edge/mediapipe/solutions/setup_cpp_python)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/concepts/)
