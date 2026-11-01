$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root
if (-not (Test-Path (Join-Path $Root "frontend\dist\index.html"))) {
    throw "找不到前端編譯輸出，請先執行 scripts/windows/build-web.ps1"
}

uv run alembic upgrade head
Write-Host "Flowfolio 正式服務將啟動於 http://127.0.0.1:8000" -ForegroundColor Green
uv run uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1

