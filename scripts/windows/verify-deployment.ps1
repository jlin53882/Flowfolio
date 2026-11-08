$ErrorActionPreference = "Continue"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root
. (Join-Path $PSScriptRoot "flowfolio-env.ps1")
$FlowfolioSettings = Get-FlowfolioSettings -Root $Root
$failures = New-Object System.Collections.Generic.List[string]

if (-not (Test-Path (Join-Path $Root "frontend\dist\index.html"))) { $failures.Add("缺少 frontend/dist/index.html") }
if (-not (Test-Path -LiteralPath $FlowfolioSettings.DataDir)) { New-Item -ItemType Directory -Force -Path $FlowfolioSettings.DataDir | Out-Null }
$backupDirectory = Join-Path $FlowfolioSettings.DataDir "backups"
if (-not (Test-Path -LiteralPath $backupDirectory)) { New-Item -ItemType Directory -Force -Path $backupDirectory | Out-Null }

try {
    $health = Invoke-RestMethod -Uri $FlowfolioSettings.LocalHealthUrl -TimeoutSec 5
    if ($health.status -ne "ok") { $failures.Add("健康端點回應不是 ok") }
    else { Write-Host "健康端點：正常" -ForegroundColor Green }
} catch { $failures.Add("無法連線到 $($FlowfolioSettings.LocalHealthUrl)") }

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

