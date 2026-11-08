[CmdletBinding()]
param(
    [Nullable[int]]$Port = $null
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root
. (Join-Path $PSScriptRoot "flowfolio-env.ps1")
. (Join-Path $PSScriptRoot "flowfolio-webhook.ps1")
$FlowfolioSettings = Get-FlowfolioSettings -Root $Root
$EffectivePort = $FlowfolioSettings.Port
$FunnelPort = $FlowfolioSettings.FunnelPort
if ($PSBoundParameters.ContainsKey("Port")) {
    if ($Port -lt 1 -or $Port -gt 65535) {
        throw "Port 必須是 1 到 65535 的整數。"
    }
    $EffectivePort = [int]$Port
    Set-Item -Path "Env:FLOWFOLIO_PORT" -Value ([string]$EffectivePort)
}
$LocalHealthUrl = Get-FlowfolioLocalHealthUrl -Settings $FlowfolioSettings -Port $EffectivePort
$ReportDirectory = Join-Path $Root "reports"
$LogFile = Join-Path $ReportDirectory "public-funnel.log"
$FunnelStateFile = Join-Path $ReportDirectory "flowfolio-funnel-state.json"
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

function Test-LocalService {
    try {
        $health = Invoke-RestMethod -Uri $LocalHealthUrl -TimeoutSec 3
        return $health.status -eq "ok"
    } catch {
        return $false
    }
}

function Get-FlowfolioFunnelState {
    if (-not (Test-Path -LiteralPath $FunnelStateFile)) {
        return $null
    }

    try {
        return (Get-Content -LiteralPath $FunnelStateFile -Raw -Encoding UTF8 | ConvertFrom-Json)
    } catch {
        return $null
    }
}

function Assert-FunnelPortAvailable {
    $status = Get-FlowfolioFunnelStatus -TailscalePath $TailscalePath
    if (-not $status) {
        return
    }

    $endpoint = Get-FlowfolioFunnelEndpoint -Status $status -Port $FunnelPort
    if ($endpoint) {
        $state = Get-FlowfolioFunnelState
        $ownsEndpoint = $state -and
            ([int]$state.FunnelPort -eq $FunnelPort) -and
            ([int]$state.LocalPort -eq $EffectivePort)
        if (-not $ownsEndpoint) {
            throw "Tailscale Funnel HTTPS port $FunnelPort 已被其他服務使用；Flowfolio 不會覆蓋既有設定。請在 .env 設定未使用的 FLOWFOLIO_FUNNEL_PORT。"
        }
        return
    }

    if ($status.TCP -and $status.TCP.PSObject.Properties[$FunnelPort.ToString()]) {
        throw "Tailscale Funnel port $FunnelPort 已被其他 TCP 服務使用；Flowfolio 不會覆蓋既有設定。請在 .env 設定未使用的 FLOWFOLIO_FUNNEL_PORT。"
    }
}

function Start-LocalService {
    if (Test-LocalService) {
        Write-Log "本機服務已在執行（$LocalHealthUrl）。" Green
        return
    }

    $serverScript = Join-Path $PSScriptRoot "start-prod.ps1"
    if (-not (Test-Path -LiteralPath $serverScript)) {
        throw "找不到正式服務啟動腳本：$serverScript"
    }

    Write-Log "尚未找到本機服務，正在背景啟動 $($FlowfolioSettings.Host):$EffectivePort。" Yellow
    $quotedServerScript = '"{0}"' -f $serverScript
    $serverProcess = Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $quotedServerScript) -WorkingDirectory $Root -WindowStyle Hidden -PassThru
    Write-Log "正式服務啟動程序已建立（PID：$($serverProcess.Id)），等待健康檢查。" Cyan

    for ($attempt = 1; $attempt -le 30; $attempt++) {
        Start-Sleep -Seconds 1
        if (Test-LocalService) {
            Write-Log "本機服務已就緒（$LocalHealthUrl）。" Green
            return
        }
    }

    throw "本機服務在 30 秒內沒有通過健康檢查，請查看 reports\server-prod.log。"
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

    Assert-FunnelPortAvailable
    Write-Log "===== Flowfolio 公開外網啟動 $(Get-Date -Format o) =====" Cyan
    Write-Log "確認 Tailscale 連線：" Cyan
    $tailscaleIp = Invoke-TailscaleCommand @("ip", "-4")
    if (-not $tailscaleIp) {
        throw "Tailscale 尚未連線，請先從 Tailscale 圖示登入並確認 Connected。"
    }

    Start-LocalService
    Write-Log "啟動 Tailscale Funnel；這會讓網址公開到網際網路。" Yellow
    # 使用 --yes 跳過命令列更新提示；首次使用仍可能需要開啟 Tailscale 授權頁一次。
    Invoke-TailscaleCommand @("funnel", "--yes", "--bg", "--https=$FunnelPort", $EffectivePort) | Out-Null
    [pscustomobject]@{
        FunnelPort = $FunnelPort
        LocalPort = $EffectivePort
        StartedAt = (Get-Date -Format o)
    } | ConvertTo-Json | Set-Content -LiteralPath $FunnelStateFile -Encoding UTF8
    Write-Log "Funnel 已設定，以下是目前狀態與手機網址：" Green
    Invoke-TailscaleCommand @("funnel", "status") | Out-Null
    $status = Get-FlowfolioFunnelStatus -TailscalePath $TailscalePath
    $publicUrl = if ($status) {
        Get-FlowfolioFunnelPublicUrl -Status $status -Port $FunnelPort
    } else {
        $null
    }
    if ($publicUrl) {
        Write-Log "Flowfolio 公開網址：$publicUrl" Green
        if ([string]::IsNullOrWhiteSpace($FlowfolioSettings.WebhookUrl)) {
            Write-Log "未設定 FLOWFOLIO_WEBHOOK_URL，略過 webhook 通知。" Gray
        } elseif (Send-FlowfolioWebhook -WebhookUrl $FlowfolioSettings.WebhookUrl -PublicUrl $publicUrl) {
            Write-Log "Flowfolio webhook 通知已送出。" Green
        } else {
            Write-Log "Flowfolio webhook 通知失敗；公開 Funnel 仍維持啟動。" Yellow
        }
    } else {
        Write-Log "找不到 Flowfolio Funnel 公開網址，略過 webhook 通知。" Yellow
    }
    Write-Log "Flowfolio Funnel 使用 Tailscale HTTPS port $FunnelPort；其他服務的 Funnel 設定不會被重設。" Cyan
    Write-Log "手機不需要安裝 Tailscale，使用瀏覽器開啟上方 https://...ts.net 網址即可。" Cyan
    Write-Log "停止 Flowfolio 公開外網：scripts/windows/stop-public-funnel.ps1" Yellow
    Write-Log "記錄檔：$LogFile" Gray
} catch {
    Write-Log "公開外網啟動失敗：$($_.Exception.Message)" Red
    exit 1
}
