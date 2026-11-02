$ErrorActionPreference = "Continue"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root
$failures = New-Object System.Collections.Generic.List[string]

if (-not (Test-Path (Join-Path $Root "frontend\dist\index.html"))) { $failures.Add("缺少 frontend/dist/index.html") }
if (-not (Test-Path (Join-Path $Root "data"))) { New-Item -ItemType Directory -Force (Join-Path $Root "data") | Out-Null }
if (-not (Test-Path (Join-Path $Root "data\backups"))) { New-Item -ItemType Directory -Force (Join-Path $Root "data\backups") | Out-Null }

try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5
    if ($health.status -ne "ok") { $failures.Add("健康端點回應不是 ok") }
    else { Write-Host "健康端點：正常" -ForegroundColor Green }
} catch { $failures.Add("無法連線到 http://127.0.0.1:8000/health") }

if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv run alembic current
} else { $failures.Add("找不到 uv") }

if (Get-Command tailscale -ErrorAction SilentlyContinue) {
    # Tailscale 1.98.x 的 Serve/Funnel 查詢會回傳同一份服務入口設定，避免重複列印。
    Write-Host "Tailscale Serve／Funnel 狀態：以下為本機查詢結果" -ForegroundColor Cyan
    tailscale funnel status
} else { Write-Host "Tailscale：未安裝或不在 PATH，未驗證" -ForegroundColor Yellow }

if ($failures.Count -gt 0) {
    Write-Host "部署驗證失敗：" -ForegroundColor Red
    $failures | ForEach-Object { Write-Host "- $_" -ForegroundColor Red }
    exit 1
}
Write-Host "部署基本驗證完成。" -ForegroundColor Green

