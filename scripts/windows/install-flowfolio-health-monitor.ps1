[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root
. (Join-Path $PSScriptRoot "flowfolio-env.ps1")
$FlowfolioSettings = Get-FlowfolioSettings -Root $Root

$MonitorScript = Join-Path $PSScriptRoot "monitor-flowfolio-health.ps1"
$TaskName = "Flowfolio-健康監控"
$Quote = [char]34
$TaskArguments = "-NoProfile -ExecutionPolicy Bypass -File $Quote$MonitorScript$Quote -Once"

if (-not (Test-Path -LiteralPath $MonitorScript)) {
    throw "找不到監控腳本：$MonitorScript"
}

Write-Host "正在註冊 Flowfolio 每 10 分鐘健康監控..." -ForegroundColor Cyan
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $TaskArguments
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration (New-TimeSpan -Days 3650)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null

Write-Host "工作排程器註冊完成：$TaskName" -ForegroundColor Green
Write-Host "現在先執行一次監控驗證。" -ForegroundColor Cyan
Start-ScheduledTask -TaskName $TaskName
Write-Host "設定完成；之後每 10 分鐘自動檢查本機 $($FlowfolioSettings.LocalHost):$($FlowfolioSettings.Port) 與公開 Funnel。" -ForegroundColor Green
