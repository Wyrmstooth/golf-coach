# 🚀 Deploy to Render.com (FREE)

This guide walks you through deploying GolfCoach AI to **Render.com** for completely free hosting.

## ✅ What You Get (Free Tier)

- ✅ **Free PostgreSQL database** (0.5GB)
- ✅ **Free web service** hosting (auto-scales, sleeps after 15 min inactivity)
- ✅ **Custom domain** support  
- ✅ **Auto-deploys** from GitHub on push
- ✅ **Free SSL certificate** (HTTPS)

## 📋 Prerequisites

1. **GitHub account** (to push your code)
2. **Render.com account** (sign up free at https://render.com)
3. **Your repo on GitHub** (public or private)

Important: use the same repository this workspace pushes to: `zainulabidin776/golf-dashboard`.
If Render is connected to a different repo, it will keep deploying stale requirements and the Python version fixes will never apply.

---

## 🔧 Step 1: Prepare Your Repository

### 1.1 Update Backend Dependencies
Add PostgreSQL driver:

```bash
cd backend
# Add to requirements_api.txt:
echo "psycopg2-binary>=2.9.9,<3.0.0" >> requirements_api.txt
```

### 1.2 Update Backend Code (Database Connection)

Edit `backend/database.py` — change SQLite to PostgreSQL:

```python
# OLD:
# SQLALCHEMY_DATABASE_URL = "sqlite:///./golf.db"

# NEW:
import os
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./golf.db"  # fallback for local dev
)

# Remove the SQLite check:
# if "sqlite" in SQLALCHEMY_DATABASE_URL:
#     connect_args = {"check_same_thread": False}
# else:
#     connect_args = {}

# Make sure to handle both:
connect_args = {} if "postgresql" in SQLALCHEMY_DATABASE_URL else {"check_same_thread": False}
```

### 1.3 Push to GitHub

```bash
git add .
git commit -m "Add deployment configuration"
git push origin main
```

---

## 🚀 Step 2: Deploy on Render

### 2.1 Create Backend Service

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Select **"GitHub"** and authorize
4. Find your repo `golf-dashboard`
5. Fill in:
   - **Name:** `golfcoach-backend`
   - **Runtime:** `Python 3.10`
   - **Build Command:** 
     ```
  pip install --no-cache-dir --prefer-binary -r requirements.txt -r backend/requirements_api.txt
     ```
   - **Start Command:**
     ```
     python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan:** Select **Free**

### 2.2 Add Environment Variables

Click **"Environment"** tab, add these:

| Key | Value |
|-----|-------|
| `PYTHONUNBUFFERED` | `1` |
| `MPLBACKEND` | `Agg` |
| `ENVIRONMENT` | `production` |
| `SECRET_KEY` | *(leave blank — you'll generate it)* |
| `ALLOWED_ORIGINS` | `https://golfcoach-frontend.onrender.com` |

### 2.3 Create PostgreSQL Database

1. Go to https://dashboard.render.com
2. Click **"PostgreSQL"** → **"Create"**
3. Fill in:
   - **Name:** `golfcoach-db`
   - **Plan:** **Free**
   - **Region:** Same as your backend (e.g., Oregon)
4. Click **"Create Database"**
5. Copy the **Internal Database URL** → paste in `DATABASE_URL` env var

### 2.4 Deploy Frontend

1. Click **"New +"** → **"Static Site"**
2. Select your GitHub repo
3. Fill in:
   - **Name:** `golfcoach-frontend`
   - **Build Command:**
     ```
     cd frontend && npm install && npm run build
     ```
   - **Publish Directory:** `frontend/dist`
   - **Plan:** **Free**
4. Click **"Create Static Site"**

### 2.5 Update Backend CORS Settings

In Render dashboard for backend service:
1. Go to **Environment** → edit `ALLOWED_ORIGINS`
2. Set to: `https://golfcoach-frontend.onrender.com`

---

## ✅ Done! Test Your Deployment

After ~10 minutes:

- **Backend:** `https://golfcoach-backend.onrender.com`
- **Frontend:** `https://golfcoach-frontend.onrender.com`
- **API Docs:** `https://golfcoach-backend.onrender.com/docs`

---

## 📝 Important Notes

### Free Tier Limitations
- **Spins down** after 15 min inactivity (first request takes ~30 sec to wake up)
- **0.5GB database** limit (~50k swings max)
- **Shared CPU**, not guaranteed performance

### Scale Up Later
1. Click service → **"Plan"** → choose **"Pro"** ($7/month)
2. No additional code changes needed

### Custom Domain
1. In Render dashboard → service settings
2. Add custom domain → follow DNS setup

---

## 🔄 Auto-Deploy on Push

Every time you push to GitHub:
```bash
git push origin main
```

Render automatically redeploys! ✨

---

## ❌ Troubleshooting

### View Logs
Render dashboard → service → **"Logs"** tab

### Service won't start
- Check **Build Command** logs
- Verify `requirements.txt` versions
- Check `DATABASE_URL` is set correctly

### Frontend can't reach backend
- Verify `ALLOWED_ORIGINS` includes frontend URL
- Check backend is actually running in logs

---

## 📚 Next Steps

- Set a **custom domain** (Render docs → Domain)
- Add **error monitoring** (Sentry, etc.)
- Enable **automatic backups** for PostgreSQL
- Consider scaling to **Pro** for better performance
