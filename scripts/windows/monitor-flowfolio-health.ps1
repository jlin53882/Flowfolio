[CmdletBinding()]
param(
    [switch]$Once
)

$ErrorActionPreference = "Continue"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root
. (Join-Path $PSScriptRoot "flowfolio-env.ps1")
$FlowfolioSettings = Get-FlowfolioSettings -Root $Root
$ReportDirectory = Join-Path $Root "reports"
$LogFile = Join-Path $ReportDirectory "health-monitor.log"
$FunnelStateFile = Join-Path $ReportDirectory "flowfolio-funnel-state.json"
$StartScript = Join-Path $PSScriptRoot "start-public-funnel.ps1"
$LocalHealthUrl = $FlowfolioSettings.LocalHealthUrl
$TailscalePath = "C:\Program Files\Tailscale\tailscale.exe"
$MutexName = "Local\Flowfolio-Health-Monitor"

New-Item -ItemType Directory -Force -Path $ReportDirectory | Out-Null

function Write-Log {
    param(
        [string]$Message,
        [ConsoleColor]$Color = "Gray"
    )

    $line = "$(Get-Date -Format o) $Message"
    $line | Add-Content -LiteralPath $LogFile -Encoding UTF8
    Write-Host $line -ForegroundColor $Color
}

function Test-HealthUrl {
    param([string]$Url)

    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 300
    } catch {
        return $false
    }
}

function Test-LocalHealth {
    try {
        $health = Invoke-RestMethod -Uri $LocalHealthUrl -TimeoutSec 5
        return $health.status -eq "ok"
    } catch {
        return $false
    }
}

function Get-FunnelHealthUrl {
    if (-not (Test-Path -LiteralPath $TailscalePath)) {
        return $null
    }
    if (-not (Test-Path -LiteralPath $FunnelStateFile)) {
        return $null
    }

    try {
        $funnelState = Get-Content -LiteralPath $FunnelStateFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if ([int]$funnelState.FunnelPort -ne $FlowfolioSettings.FunnelPort -or [int]$funnelState.LocalPort -ne $FlowfolioSettings.Port) {
            return $null
        }
        $jsonLines = & $TailscalePath funnel status --json 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $jsonLines) {
            return $null
        }

        $status = ($jsonLines -join [Environment]::NewLine) | ConvertFrom-Json
        $entry = Get-FlowfolioFunnelEndpoint -Status $status -Port $FlowfolioSettings.FunnelPort
        if (-not $entry) {
            return $null
        }

        $publicUrl = Get-FlowfolioFunnelPublicUrl -Status $status -Port $FlowfolioSettings.FunnelPort
        return "$publicUrl/health"
    } catch {
        return $null
    }
}

function Invoke-Recovery {
    if (-not (Test-Path -LiteralPath $StartScript)) {
        Write-Log "找不到公開網站啟動腳本：$StartScript" Red
        return $false
    }

    Write-Log "健康檢查失敗，執行公開網站啟動腳本進行自動復原。" Yellow
    $output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StartScript 2>&1
    foreach ($line in $output) {
        [string]$line | Add-Content -LiteralPath $LogFile -Encoding UTF8
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Log "自動復原完成。" Green
        return $true
    }

    Write-Log "自動復原失敗；請確認 Tailscale 已顯示 Connected。" Red
    return $false
}

$monitorMutex = New-Object System.Threading.Mutex($false, $MutexName)
if (-not $monitorMutex.WaitOne(0)) {
    Write-Log "已有另一個監控程序執行中，本輪略過。" Yellow
    exit 0
}

try {
    Write-Log "===== Flowfolio 健康監控開始 =====" Cyan

    $localHealthy = Test-LocalHealth
    $funnelHealthUrl = Get-FunnelHealthUrl
    $funnelHealthy = $false
    if ($funnelHealthUrl) {
        $funnelHealthy = Test-HealthUrl -Url $funnelHealthUrl
    }

    Write-Log "本機健康：$localHealthy；公開 Funnel：$funnelHealthy。" Gray

    if (-not $localHealthy -or -not $funnelHealthy) {
        Invoke-Recovery | Out-Null
    } else {
        Write-Log "本輪健康檢查通過。" Green
    }
} catch {
    Write-Log "監控執行失敗：$($_.Exception.Message)" Red
} finally {
    $monitorMutex.ReleaseMutex()
    $monitorMutex.Dispose()
}
