# Railway Deployment Guide for GolfCoach AI

This guide is for the simple setup you want:

- **One Railway backend service**
- **One Railway PostgreSQL database**
- **Frontend stays on Render**
- **No Railway worker service**

That matches the current `master` branch and avoids the queue/worker complexity.

## Why This Setup

The repo already has a Dockerfile that pins Python 3.10 and installs the Linux libraries MediaPipe needs. That is the safest way to run the backend on Railway.

Do **not** choose a random Python runtime if Railway offers one. Use the Dockerfile-based deployment.

## 1. Create The Railway Project

1. Sign in to Railway.
2. Create a new project.
3. Connect your GitHub repo: `zainulabidin776/golf-dashboard`.
4. Let Railway detect the `Dockerfile` in the repository root.
5. Create the backend service first.

## 2. Backend Service Settings

Name the service something like `golfcoach-backend`.

Use these settings:

- **Source**: GitHub repo
- **Build**: Dockerfile from repo root
- **Start command**: leave default if Railway uses the Dockerfile, or use:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

- **Region**: choose the closest region to your users or database

### Backend Environment Variables

Set these on the backend service:

| Key | Value | Notes |
|-----|-------|-------|
| `DATABASE_URL` | Railway Postgres connection string | Required for production |
| `SECRET_KEY` | Random long secret | JWT signing key |
| `ALLOWED_ORIGINS` | Your Render frontend URL | Comma-separated if you have more than one |
| `ENVIRONMENT` | `production` | Enables production behavior |
| `PYTHONUNBUFFERED` | `1` | Better logs |
| `MPLBACKEND` | `Agg` | Non-GUI matplotlib backend |

You do **not** need `ANALYSIS_EXECUTION_MODE` or `ANALYSIS_WORKER_SECRET` for this setup.

## 3. Add PostgreSQL

1. Add a new PostgreSQL service to the same Railway project.
2. Let Railway generate the connection string.
3. Copy the database URL into the backend `DATABASE_URL` env var.

## 4. Frontend Stays On Render

Keep the frontend on Render as you wanted.

### Set Render Frontend API URL

In your Render frontend static site, set:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://your-railway-backend-url/api` |

Important: this value must end with `/api`. If it is just the backend root URL, the frontend will send requests to `/analyze` instead of `/api/analyze`, which causes the 404 you saw.

### Set Railway Backend CORS

In Railway backend env vars, set `ALLOWED_ORIGINS` to your Render frontend URL, for example:

```text
https://golf-coach-frontend.onrender.com
```

If you have multiple frontend URLs, separate them with commas.

## 5. What To Ignore

Ignore anything about:

- worker services
- Colab
- remote job queues
- `ANALYSIS_EXECUTION_MODE`
- `ANALYSIS_WORKER_SECRET`

That stuff is for the alternate queue-based branch, not this simplified Railway deployment.

## 6. Test Checklist

1. Open the Railway backend URL.
2. Verify `/api/health` returns JSON.
3. Open the Render frontend.
4. Log in.
5. Upload a swing video.
6. Confirm analysis starts and the status updates.
7. Check Railway logs if anything fails.

## 7. Common Gotchas

- If the backend cannot connect to the database, double-check `DATABASE_URL`.
- If login works but analysis fails, check `SECRET_KEY` and `ALLOWED_ORIGINS`.
- If Railway asks you to pick a Python runtime, stick with the Dockerfile path.
- If frontend requests fail, make sure `VITE_API_URL` points at the Railway backend and `ALLOWED_ORIGINS` includes the Render domain.

## 8. Lowest-Risk Path

If your goal is to get live quickly on Railway Hobby:

- Use one backend service.
- Use one Railway Postgres database.
- Keep the frontend on Render.
- Do not add a worker service.

That is the cleanest setup for the current codebase.
