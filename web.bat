@echo off
cd /d "%~dp0"
title XSignals Remote Panel
echo ============================================
echo   XSignals Remote Panel
echo ============================================
echo.
echo   Local : http://127.0.0.1:5000
echo   Phone : http://[your-Tailscale-IP]:5000
echo.
echo   Keep this window open. Close it to stop.
echo ============================================
echo.
"%~dp0venv\Scripts\python.exe" "%~dp0src\app.py"
pause