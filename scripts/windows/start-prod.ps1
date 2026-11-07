$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root
$ReportDirectory = Join-Path $Root "reports"
$ServerLog = Join-Path $ReportDirectory "server-prod.log"
New-Item -ItemType Directory -Force -Path $ReportDirectory | Out-Null
if (-not (Test-Path (Join-Path $Root "frontend\dist\index.html"))) {
    throw "找不到前端編譯輸出，請先執行 scripts/windows/build-web.ps1"
}

uv run alembic upgrade head
Write-Host "Flowfolio 正式服務將啟動於 http://127.0.0.1:8000" -ForegroundColor Green
"===== Flowfolio 正式服務啟動 $(Get-Date -Format o) =====" | Tee-Object -FilePath $ServerLog -Append
& uv run uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1 --log-level info --access-log 2>&1 |
    Tee-Object -FilePath $ServerLog -Append
$ServerExitCode = $LASTEXITCODE
if ($ServerExitCode -ne 0) {
    throw "Flowfolio 正式服務已停止，退出碼：$ServerExitCode。請查看 $ServerLog"
}

