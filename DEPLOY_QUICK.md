# 🚀 QUICK START: Deploy to Render.com (5 Min Setup)

## **TL;DR — Just Follow These Steps**

### 1. Push Your Code to GitHub
```bash
cd golf-dashboard
git add .
git commit -m "Deploy: add Dockerfile and configs"
git push origin main
```

### 2. Create Free Account
- Go to https://render.com
- Sign up with GitHub
- Click **"Authorize"** to connect your account

### 3. Deploy Backend
1. Click **"New +"** → **"Web Service"**
2. Select your `golf-dashboard` repo
3. Fill in:
   - **Name:** `golfcoach-backend` 
   - **Runtime:** `Python 3.10`
   - **Build Command:** `pip install -r requirements.txt -r backend/requirements_api.txt`
   - **Start Command:** `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** `Free`
4. Click **"Create Web Service"** (wait 5-10 min)

### 4. Create PostgreSQL Database
1. Click **"New +"** → **"PostgreSQL"**
2. Fill in:
   - **Name:** `golfcoach-db`
   - **Plan:** `Free`
   - **Region:** `Oregon` (or same as backend)
3. Click **"Create Database"** (wait 2-3 min)
4. Copy the **"Internal Database URL"** (format: `postgresql://...`)

### 5. Connect Database to Backend
1. Go to backend service → **"Environment"** tab
2. Click **"Add Environment Variable"**
3. Add:
   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | `postgresql://...` ← paste from step 4 |
   | `PYTHONUNBUFFERED` | `1` |
   | `MPLBACKEND` | `Agg` |
   | `ENVIRONMENT` | `production` |

4. Click **"Save"** (service will auto-redeploy)

### 6. Deploy Frontend
1. Click **"New +"** → **"Static Site"**
2. Select your `golf-dashboard` repo
3. Fill in:
   - **Name:** `golfcoach-frontend`
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Publish Directory:** `frontend/dist`
   - **Plan:** `Free`
4. Click **"Create Static Site"** (wait 3-5 min)

### 7. Update Backend CORS
Back in backend service environment:
1. Edit `ALLOWED_ORIGINS` variable
2. Change to: `https://golfcoach-frontend.onrender.com` (replace with your actual frontend URL from step 6)
3. Click **"Save"**

---

## ✅ Done!

After everything deploys (~15-20 min total):

### **Your URLs:**
- **App:** `https://golfcoach-frontend.onrender.com` ← **Open this!**
- **API:** `https://golfcoach-backend.onrender.com`
- **API Docs:** `https://golfcoach-backend.onrender.com/docs`

### **Test It:**
1. Open the frontend URL
2. Register a new account
3. Upload a golf swing video
4. See the magic ✨

---

## ⚠️ Common Issues

### **"Cannot GET /"**
- Frontend still building, wait 2-3 more minutes

### **"Connection refused" error in app**
- `ALLOWED_ORIGINS` not set correctly
- Use frontend URL from your Render dashboard
- Check `DATABASE_URL` is set in backend

### **"No module named X"**
- Check Build Command has both requirements:
  ```
  pip install -r requirements.txt -r backend/requirements_api.txt
  ```

### **View Logs**
Click service → **"Logs"** tab to debug issues

---

## 🔄 Auto-Deploy Feature

After this initial setup, every push to GitHub auto-deploys:

```bash
git push origin main
```

Wait ~3-5 min and your changes go live! 🎉

---

## 💰 Cost

**Completely free forever:**
- ✅ Both services (backend + frontend)
- ✅ PostgreSQL database (0.5GB)
- ✅ SSL certificate
- ✅ Auto-deploy on push

No credit card needed!

---

## 📈 Scale Up Later (Optional)

If you want better performance:
1. Backend: Free → Pro ($7/month)
2. Database: Free → Standard ($15/month)
3. Frontend: Free tier is fast enough

---

## 🆘 Still Stuck?

Check [DEPLOY_RENDER.md](DEPLOY_RENDER.md) for detailed troubleshooting.
