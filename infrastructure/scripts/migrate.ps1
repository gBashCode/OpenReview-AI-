# ==============================================================================
# OpenReview AI - Automated Database Migration Runner (PowerShell)
# ==============================================================================
param(
    [string]$ConfigPath = "backend/alembic.ini"
)

$ErrorActionPreference = "Stop"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " Starting Database Migrations with Alembic" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$maxRetries = 30
$retryInterval = 2
$connected = $false

Write-Host "Checking database connectivity..." -ForegroundColor Yellow

for ($i = 1; $i -le $maxRetries; $i++) {
    try {
        $env:PYTHONPATH = "backend;$PSScriptRoot/../../backend"
        $output = & .venv\Scripts\python -c "import asyncio; from app.database.session import check_db_connectivity; assert asyncio.run(check_db_connectivity())" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $connected = $true
            break
        }
    } catch {
        # ignore and retry
    }
    Write-Host "Waiting for database to accept connections ($i/$maxRetries)..." -ForegroundColor DarkGray
    Start-Sleep -Seconds $retryInterval
}

if (-not $connected) {
    Write-Error "Database connectivity failed after $($maxRetries * $retryInterval) seconds."
    exit 1
}

Write-Host "Database is ready. Executing 'alembic upgrade head'..." -ForegroundColor Green
& .venv\Scripts\alembic.exe -c $ConfigPath upgrade head

if ($LASTEXITCODE -eq 0) {
    Write-Host "======================================================================" -ForegroundColor Green
    Write-Host " Database Migrations Completed Successfully!" -ForegroundColor Green
    Write-Host "======================================================================" -ForegroundColor Green
} else {
    Write-Error "Alembic migration failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}
