@echo off
chcp 65001 >nul
title Flowfolio - 公開外網啟動（Tailscale Funnel）
cd /d "%~dp0..\.."

echo ============================================
echo Flowfolio - 公開外網啟動（Tailscale Funnel）
echo ============================================
echo.
echo 注意：Funnel 會讓網站公開到網際網路，請勿分享給不信任的人。
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-public-funnel.ps1"
if errorlevel 1 (
    echo.
    echo 公開外網啟動失敗，請查看 reports\public-funnel.log
    pause
    exit /b 1
)

echo.
echo 公開外網已設定；關閉此視窗不會停止背景 Funnel。
echo 停止方式：tailscale funnel reset
pause
