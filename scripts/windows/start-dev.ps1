$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root
$ReportDirectory = Join-Path $Root "reports"
$ServerLog = Join-Path $ReportDirectory "server-dev.log"
New-Item -ItemType Directory -Force -Path $ReportDirectory | Out-Null

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
"===== Flowfolio 開發服務啟動 $(Get-Date -Format o) =====" | Tee-Object -FilePath $ServerLog -Append
& uv run uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1 --log-level info --access-log 2>&1 |
    Tee-Object -FilePath $ServerLog -Append
$ServerExitCode = $LASTEXITCODE
if ($ServerExitCode -ne 0) {
    throw "Flowfolio 開發服務已停止，退出碼：$ServerExitCode。請查看 $ServerLog"
}

