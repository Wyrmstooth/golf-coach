# GolfCoach AI - Startup Script (PowerShell)
# ============================================================
# Run from the golf_optimized/ directory:
#   powershell -ExecutionPolicy Bypass -File start_app.ps1
#
# REQUIREMENTS:
#   - Your conda/venv environment must be activated BEFORE running this script
#     so that mediapipe, sklearn, torch, ultralytics, etc. are available.
#   - Example:
#       conda activate <your-env>
#       powershell -ExecutionPolicy Bypass -File start_app.ps1
# ============================================================

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT

Write-Host ""
Write-Host "====================================" -ForegroundColor Green
Write-Host "  GolfCoach AI - Starting Services  " -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

# Verify Python has the required packages
$check = python -c "import fastapi, sklearn, cv2, mediapipe; print('OK')" 2>&1
if ($check -ne "OK") {
    Write-Host "ERROR: Required Python packages are missing." -ForegroundColor Red
    Write-Host "Please activate your conda environment first:" -ForegroundColor Yellow
    Write-Host "  conda activate <your-env>" -ForegroundColor Cyan
    Write-Host "Then install backend deps:" -ForegroundColor Yellow
    Write-Host "  pip install -r backend/requirements_api.txt" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Missing: $check" -ForegroundColor Red
    exit 1
}

# Start FastAPI backend
Write-Host "Starting backend on http://localhost:8000 ..." -ForegroundColor Cyan
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:ROOT
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
}

Start-Sleep -Seconds 3

# Check backend started
try {
    $health = Invoke-WebRequest -Uri http://localhost:8000/api/health -UseBasicParsing -ErrorAction Stop
    Write-Host "  Backend OK: $($health.Content)" -ForegroundColor Green
} catch {
    Write-Host "  Backend failed to start. Check Python environment." -ForegroundColor Red
}

# Start React frontend
Write-Host "Starting frontend on http://localhost:5173 ..." -ForegroundColor Cyan
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "$using:ROOT\frontend"
    npm run dev
}

Start-Sleep -Seconds 4
Write-Host ""
Write-Host "Both servers are running!" -ForegroundColor Green
Write-Host "  Frontend : http://localhost:5173" -ForegroundColor Yellow
Write-Host "  Backend  : http://localhost:8000" -ForegroundColor Yellow
Write-Host "  API Docs : http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop." -ForegroundColor White

try {
    Wait-Job $backendJob, $frontendJob
} finally {
    Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Write-Host "Servers stopped." -ForegroundColor Red
}
