# Start the GolfCoach FastAPI backend using the golfpose conda environment.
# Run from the project root:
#   powershell -ExecutionPolicy Bypass -File start_backend.ps1

$ROOT      = Split-Path -Parent $MyInvocation.MyCommand.Path
$GOLFPOSE  = "$env:USERPROFILE\miniconda3\envs\golfpose\python.exe"

# Fallback: try anaconda3
if (-not (Test-Path $GOLFPOSE)) {
    $GOLFPOSE = "$env:USERPROFILE\anaconda3\envs\golfpose\python.exe"
}

if (-not (Test-Path $GOLFPOSE)) {
    Write-Host "ERROR: golfpose Python not found." -ForegroundColor Red
    Write-Host "Create it with:  conda create -n golfpose python=3.10 -y" -ForegroundColor Yellow
    Write-Host "Then install:    pip install -r requirements.txt -r backend/requirements_api.txt" -ForegroundColor Yellow
    exit 1
}

$pyVersion = & $GOLFPOSE --version
Write-Host "Using $pyVersion at $GOLFPOSE" -ForegroundColor Green

Set-Location $ROOT
& $GOLFPOSE -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
