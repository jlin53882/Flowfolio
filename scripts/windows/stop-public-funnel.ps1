$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root
. (Join-Path $PSScriptRoot "flowfolio-env.ps1")
$FlowfolioSettings = Get-FlowfolioSettings -Root $Root
$ReportDirectory = Join-Path $Root "reports"
$FunnelStateFile = Join-Path $ReportDirectory "flowfolio-funnel-state.json"

if (-not (Test-Path -LiteralPath $FunnelStateFile)) {
    Write-Host "找不到 Flowfolio Funnel 狀態檔，未修改其他 Tailscale Funnel 設定。" -ForegroundColor Yellow
    exit 0
}

try {
    $funnelState = Get-Content -LiteralPath $FunnelStateFile -Raw -Encoding UTF8 | ConvertFrom-Json
} catch {
    throw "Flowfolio Funnel 狀態檔無法讀取，為避免影響其他服務，停止操作。"
}
if ([int]$funnelState.FunnelPort -ne $FlowfolioSettings.FunnelPort) {
    throw "Flowfolio Funnel 狀態與目前 FLOWFOLIO_FUNNEL_PORT 不一致，為避免影響其他服務，停止操作。"
}

$tailscaleCommand = Get-Command tailscale -ErrorAction SilentlyContinue
if ($tailscaleCommand) {
    $TailscalePath = $tailscaleCommand.Source
} elseif (Test-Path "C:\Program Files\Tailscale\tailscale.exe") {
    $TailscalePath = "C:\Program Files\Tailscale\tailscale.exe"
} else {
    throw "找不到 Tailscale CLI，請確認 Tailscale 已安裝。"
}

$status = Get-FlowfolioFunnelStatus -TailscalePath $TailscalePath
$endpoint = if ($status) {
    Get-FlowfolioFunnelEndpoint -Status $status -Port $FlowfolioSettings.FunnelPort
} else {
    $null
}
if (-not $endpoint) {
    Write-Host "找不到 Flowfolio Funnel port $($FlowfolioSettings.FunnelPort)，未修改其他 Tailscale Funnel 設定。" -ForegroundColor Yellow
    exit 0
}

$proxyTargets = @()
if ($endpoint.Value.Handlers) {
    $proxyTargets = @(
        $endpoint.Value.Handlers.PSObject.Properties |
            ForEach-Object { $_.Value.Proxy } |
            Where-Object { $_ }
    )
}
if (-not ($proxyTargets | Where-Object { $_ -match (":$([int]$funnelState.LocalPort)") })) {
    throw "Funnel port $($FlowfolioSettings.FunnelPort) 不是 Flowfolio 的服務，為避免影響其他服務，停止操作。"
}

& $TailscalePath funnel "--https=$($FlowfolioSettings.FunnelPort)" off
if ($LASTEXITCODE -ne 0) {
    throw "停止 Tailscale Funnel 失敗。"
}
Remove-Item -LiteralPath $FunnelStateFile -Force
Write-Host "Flowfolio 公開外網已停止；其他 Tailscale Funnel 設定未變更。" -ForegroundColor Green
