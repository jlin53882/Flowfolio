$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location (Join-Path $Root "frontend")

if (-not (Test-Path (Join-Path (Get-Location) "node_modules"))) {
    npm install
}
npm run build
Write-Host "前端編譯完成：$Root\frontend\dist" -ForegroundColor Green

