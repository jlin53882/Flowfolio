$ErrorActionPreference = "Stop"
Unregister-ScheduledTask -TaskName "Flowfolio-Private-Web" -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "已移除 Flowfolio 私人網站的工作排程器工作。" -ForegroundColor Green

