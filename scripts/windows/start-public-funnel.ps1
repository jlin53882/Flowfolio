[CmdletBinding()]
param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root
$ReportDirectory = Join-Path $Root "reports"
$LogFile = Join-Path $ReportDirectory "public-funnel.log"
New-Item -ItemType Directory -Force -Path $ReportDirectory | Out-Null

function Write-Log {
    param(
        [string]$Message,
        [ConsoleColor]$Color = "Gray"
    )

    $Message | Add-Content -LiteralPath $LogFile -Encoding utf8
    Write-Host $Message -ForegroundColor $Color
}

function Invoke-TailscaleCommand {
    param([string[]]$Arguments)

    $output = & $TailscalePath @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    foreach ($line in $output) {
        $text = [string]$line
        $text | Add-Content -LiteralPath $LogFile -Encoding utf8
        Write-Host $text
    }
    if ($exitCode -ne 0) {
        throw "Tailscale 指令失敗：tailscale $($Arguments -join ' ')"
    }
    return @($output)
}

try {
    $TailscalePath = $null
    $tailscaleCommand = Get-Command tailscale -ErrorAction SilentlyContinue
    if ($tailscaleCommand) {
        $TailscalePath = $tailscaleCommand.Source
    } elseif (Test-Path "C:\Program Files\Tailscale\tailscale.exe") {
        $TailscalePath = "C:\Program Files\Tailscale\tailscale.exe"
    }
    if (-not $TailscalePath) {
        throw "找不到 Tailscale CLI，請先確認 Tailscale 已安裝並已加入 PATH。"
    }

    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $listener) {
        throw "找不到本機 $Port 服務，請先執行 .\scripts\windows\start-prod.ps1。"
    }

    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 5
    } catch {
        throw "本機服務沒有通過健康檢查：$($_.Exception.Message)"
    }
    if ($health.status -ne "ok") {
        throw "本機健康端點回應不是 ok，停止設定公開外網。"
    }

    Write-Log "===== Flowfolio 公開外網啟動 $(Get-Date -Format o) =====" Cyan
    Write-Log "本機服務：正常（127.0.0.1:$Port）" Green
    Write-Log "確認 Tailscale 連線：" Cyan
    $tailscaleIp = Invoke-TailscaleCommand @("ip", "-4")
    if (-not $tailscaleIp) {
        throw "Tailscale 尚未連線，請先從 Tailscale 圖示登入並確認 Connected。"
    }

    Write-Log "啟動 Tailscale Funnel；這會讓網址公開到網際網路。" Yellow
    # 使用 --yes 跳過命令列更新提示；首次使用仍可能需要開啟 Tailscale 授權頁一次。
    Invoke-TailscaleCommand @("funnel", "--yes", "--bg", $Port) | Out-Null
    Write-Log "Funnel 已設定，以下是目前狀態與手機網址：" Green
    Invoke-TailscaleCommand @("funnel", "status") | Out-Null
    Write-Log "手機不需要安裝 Tailscale，使用瀏覽器開啟上方 https://...ts.net 網址即可。" Cyan
    Write-Log "停止公開外網：tailscale funnel reset" Yellow
    Write-Log "記錄檔：$LogFile" Gray
} catch {
    Write-Log "公開外網啟動失敗：$($_.Exception.Message)" Red
    exit 1
}
