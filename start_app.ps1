# GolfCoach AI - Startup Script (PowerShell)
# ============================================================
# Usage:  Run this from the golf_optimized/ directory:
#
#   powershell -ExecutionPolicy Bypass -File start_app.ps1
#
# The script auto-detects your conda 'golfpose' environment.
# If your env has a different name, change CONDA_ENV below.
# ============================================================

$ROOT        = Split-Path -Parent $MyInvocation.MyCommand.Path
$CONDA_ENV   = "golfpose"
$CONDA_BASE  = "$env:USERPROFILE\miniconda3"   # change to anaconda3 if needed
$PYTHON      = "$CONDA_BASE\envs\$CONDA_ENV\python.exe"

# Fallback: if miniconda3 not found, try anaconda3
if (-not (Test-Path $PYTHON)) {
    $CONDA_BASE = "$env:USERPROFILE\anaconda3"
    $PYTHON     = "$CONDA_BASE\envs\$CONDA_ENV\python.exe"
}

# Fallback: if still not found, try the currently-active python
if (-not (Test-Path $PYTHON)) {
    $PYTHON = (Get-Command python -ErrorAction SilentlyContinue).Source
}

Set-Location $ROOT

Write-Host ""
Write-Host "====================================" -ForegroundColor Green
Write-Host "  GolfCoach AI - Starting Services  " -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host "  Python : $PYTHON" -ForegroundColor DarkGray
Write-Host ""

if (-not (Test-Path $PYTHON)) {
    Write-Host "ERROR: Cannot find Python at: $PYTHON" -ForegroundColor Red
    Write-Host "Edit the CONDA_ENV / CONDA_BASE variables in start_app.ps1" -ForegroundColor Yellow
    exit 1
}

# Verify required API packages are available in this Python
# NOTE: ML packages (sklearn, cv2, mediapipe) are lazy-loaded at analysis time,
#       so we only check for the web-server dependencies here.
$check = & $PYTHON -c "import fastapi, uvicorn; print('OK')" 2>&1
if ($check -ne "OK") {
    Write-Host "ERROR: Required API packages missing in $CONDA_ENV environment." -ForegroundColor Red
    Write-Host "Run:  conda activate $CONDA_ENV  &&  pip install -r backend/requirements_api.txt" -ForegroundColor Yellow
    Write-Host "Detail: $check" -ForegroundColor DarkGray
    exit 1
}

Write-Host "Package check passed." -ForegroundColor Green

# ---- Start FastAPI backend ----
Write-Host "Starting backend  ->  http://localhost:8000 ..." -ForegroundColor Cyan
$backendProcess = Start-Process `
    -FilePath $PYTHON `
    -ArgumentList "-m uvicorn backend.main:app --host 0.0.0.0 --port 8000" `
    -WorkingDirectory $ROOT `
    -PassThru `
    -NoNewWindow

Start-Sleep -Seconds 4

# Quick health check
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8000/api/health" `
        -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  Backend OK  ->  $($health.Content)" -ForegroundColor Green
} catch {
    Write-Host "  Backend may still be starting. Check http://localhost:8000/docs" -ForegroundColor Yellow
}

# ---- Start React frontend ----
Write-Host "Starting frontend ->  http://localhost:5173 ..." -ForegroundColor Cyan
$frontendProcess = Start-Process `
    -FilePath "npm" `
    -ArgumentList "run dev" `
    -WorkingDirectory "$ROOT\frontend" `
    -PassThru `
    -NoNewWindow

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "  Both services are running!          " -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host "  App      :  http://localhost:5173   " -ForegroundColor Yellow
Write-Host "  API docs :  http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C or close this window to stop." -ForegroundColor White

# Keep alive until the backend exits or user hits Ctrl+C
try {
    $backendProcess.WaitForExit()
} finally {
    if (-not $backendProcess.HasExited)  { $backendProcess.Kill() }
    if (-not $frontendProcess.HasExited) { $frontendProcess.Kill() }
    Write-Host "`nBoth servers stopped." -ForegroundColor Red
}
