@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title XSignals AI - Crypto Analysis Toolkit
color 0A
cd /d "%~dp0"

set "PY=venv\Scripts\python.exe"

if not exist "%PY%" (
    echo [INFO] Virtual environment not found. Creating it...
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python 3.8+ is required but not found on PATH.
        echo         Install from https://python.org and check "Add Python to PATH".
        pause
        exit /b 1
    )
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

if not exist "venv\Lib\site-packages\pandas\" (
    echo [INFO] Installing dependencies. Please wait...
    "%PY%" -m pip install -r src\requirements.txt --quiet
)

:MENU
cls
echo.
echo  ==================================================
echo    XSignals AI - Crypto Analysis Toolkit
echo  ==================================================
echo.
echo    [1] Analyze a single coin
echo    [2] Scan for opportunities
echo    [3] Multi-timeframe analysis
echo    [4] Analyze specific pairs
echo    [5] Open results folder (logs)
echo    [6] Exit
echo.
echo    Note: results are auto-saved to the logs folder.
echo.
set /p choice="Select an option (1-6): "

if "%choice%"=="1" (
    set /p symbol="Enter symbol (e.g. BTCUSDT): "
    "%PY%" src\main.py --symbol !symbol!
    pause
    goto MENU
)
if "%choice%"=="2" (
    "%PY%" src\main.py --scan
    pause
    goto MENU
)
if "%choice%"=="3" (
    set /p symbol="Enter symbol (e.g. ETHUSDT): "
    set /p timeframe="Enter timeframes separated by spaces (e.g. 15m 1h 4h 1d): "
    "%PY%" src\main.py --symbol "!symbol!" --timeframes !timeframe!
    pause
    goto MENU
)
if "%choice%"=="4" (
    set /p pairs="Enter pairs separated by spaces (e.g. BTCUSDT ETHUSDT SOLUSDT): "
    "%PY%" src\main.py --scan --pairs !pairs!
    pause
    goto MENU
)
if "%choice%"=="5" (
    if not exist "logs" mkdir logs
    explorer "%~dp0logs"
    goto MENU
)
if "%choice%"=="6" (
    echo Goodbye.
    timeout /t 1 >nul
    exit /b
)
echo Invalid selection. Please try again.
pause
goto MENU