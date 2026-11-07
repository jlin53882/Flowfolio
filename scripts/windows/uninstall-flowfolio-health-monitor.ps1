[CmdletBinding()]
param()

$TaskName = "Flowfolio-健康監控"
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
if (-not (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue)) {
    Write-Host "已解除 Flowfolio 健康監控。" -ForegroundColor Green
} else {
    Write-Host "找不到或無法解除工作：$TaskName" -ForegroundColor Yellow
}
