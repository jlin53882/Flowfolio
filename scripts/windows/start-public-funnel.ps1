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

function Test-LocalService {
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 3
        return $health.status -eq "ok"
    } catch {
        return $false
    }
}

function Start-LocalService {
    if (Test-LocalService) {
        Write-Log "本機服務已在執行（127.0.0.1:$Port）。" Green
        return
    }

    if ($Port -ne 8000) {
        throw "自動啟動正式服務目前只支援 Port 8000。"
    }

    $serverScript = Join-Path $PSScriptRoot "start-prod.ps1"
    if (-not (Test-Path -LiteralPath $serverScript)) {
        throw "找不到正式服務啟動腳本：$serverScript"
    }

    Write-Log "尚未找到本機服務，正在背景啟動 127.0.0.1:8000。" Yellow
    $quotedServerScript = '"{0}"' -f $serverScript
    $serverProcess = Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $quotedServerScript) -WorkingDirectory $Root -WindowStyle Hidden -PassThru
    Write-Log "正式服務啟動程序已建立（PID：$($serverProcess.Id)），等待健康檢查。" Cyan

    for ($attempt = 1; $attempt -le 30; $attempt++) {
        Start-Sleep -Seconds 1
        if (Test-LocalService) {
            Write-Log "本機服務已就緒（127.0.0.1:8000）。" Green
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

    Write-Log "===== Flowfolio 公開外網啟動 $(Get-Date -Format o) =====" Cyan
    Write-Log "確認 Tailscale 連線：" Cyan
    $tailscaleIp = Invoke-TailscaleCommand @("ip", "-4")
    if (-not $tailscaleIp) {
        throw "Tailscale 尚未連線，請先從 Tailscale 圖示登入並確認 Connected。"
    }

    Start-LocalService
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
