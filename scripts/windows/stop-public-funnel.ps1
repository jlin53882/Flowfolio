$ErrorActionPreference = "Stop"

$tailscaleCommand = Get-Command tailscale -ErrorAction SilentlyContinue
if ($tailscaleCommand) {
    $TailscalePath = $tailscaleCommand.Source
} elseif (Test-Path "C:\Program Files\Tailscale\tailscale.exe") {
    $TailscalePath = "C:\Program Files\Tailscale\tailscale.exe"
} else {
    throw "找不到 Tailscale CLI，請確認 Tailscale 已安裝。"
}

& $TailscalePath funnel reset
if ($LASTEXITCODE -ne 0) {
    throw "停止 Tailscale Funnel 失敗。"
}
Write-Host "Flowfolio 公開外網已停止。" -ForegroundColor Green
