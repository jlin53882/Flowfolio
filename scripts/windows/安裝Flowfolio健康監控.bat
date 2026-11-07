@echo off
chcp 65001 >nul
title Flowfolio Health Monitor Setup
cd /d "%~dp0..\.."

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-flowfolio-health-monitor.ps1"
if errorlevel 1 (
    echo.
    echo Monitor setup failed. Check reports\health-monitor.log
    pause
    exit /b 1
)

echo.
echo Flowfolio health monitor installed.
pause
