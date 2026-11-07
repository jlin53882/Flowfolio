@echo off
chcp 65001 >nul
title Flowfolio Health Monitor Removal
cd /d "%~dp0..\.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall-flowfolio-health-monitor.ps1"
pause
