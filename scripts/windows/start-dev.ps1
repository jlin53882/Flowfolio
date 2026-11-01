$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

if (-not (Test-Path (Join-Path $Root "frontend\node_modules"))) {
    Push-Location (Join-Path $Root "frontend")
    npm install
    Pop-Location
}

Push-Location (Join-Path $Root "frontend")
npm run build
Pop-Location

uv run alembic upgrade head
Write-Host "Flowfolio 開發服務將啟動於 http://127.0.0.1:8000" -ForegroundColor Green
uv run uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1

