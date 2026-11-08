@echo off
chcp 65001 >nul
title Flowfolio Public Funnel
cd /d "%~dp0..\.."

echo ============================================
echo Flowfolio Public Funnel
echo ============================================
echo.
echo Starting the public HTTPS endpoint...
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-public-funnel.ps1"
if errorlevel 1 (
    echo.
    echo Startup failed. Check reports\public-funnel.log
    pause
    exit /b 1
)

echo.
echo Public Funnel is running in the background.
echo Stop it with: scripts\windows\stop-public-funnel.ps1
pause
