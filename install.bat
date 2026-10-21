@echo off
chcp 65001 >nul
title XSignals AI - Installation
color 0A
cls
cd /d "%~dp0"

echo.
echo ██╗  ██╗███████╗██╗ ██████╗ ███╗   ██╗ █████╗ ██╗     ███████╗ █████╗ ██╗
echo ╚██╗██╔╝██╔════╝██║██╔════╝ ████╗  ██║██╔══██╗██║     ██╔════╝██╔══██╗██║
echo  ╚███╔╝ ███████╗██║██║  ███╗██╔██╗ ██║███████║██║     ███████╗███████║██║
echo  ██╔██╗ ╚════██║██║██║   ██║██║╚██╗██║██╔══██║██║     ╚════██║██╔══██║██║
echo ██╔╝ ██╗███████║██║╚██████╔╝██║ ╚████║██║  ██║███████╗███████║██║  ██║██║
echo ╚═╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝                                                      
echo.
echo ───────────────────────────────────────────────────────────────
echo           Automated Installation Environment Setup             
echo ───────────────────────────────────────────────────────────────
echo.
timeout /t 2 >nul

REM [1/5] Check Python installation
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed
    echo Please install Python 3.8+ and check "Add to PATH"
    pause
    exit /b 1
)
for /f "delims=" %%v in ('python --version') do echo %%v
echo Python found
echo.

REM [2/5] Create virtual environment
echo [2/5] Creating virtual environment...
if exist "venv\" (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    echo Virtual environment created
)
echo.

REM [3/5] Activate virtual environment
echo [3/5] Activating virtual environment...
call ".\venv\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo Activated
echo.

REM [4/5] Install dependencies
echo [4/5] Installing dependencies (this may take a minute)...
pip install -r src\requirements.txt --quiet
echo Dependencies installed successfully.
echo.

REM [5/5] Setup environment file
echo [5/5] Setting up configuration...
if exist "src\.env" (
    echo src\.env file already exists
) else (
    if exist "src\.env.example" (
        copy src\.env.example src\.env >nul
        echo Created src\.env file from template
        echo.
        echo  IMPORTANT: Edit src\.env file and add your API keys:
        echo    - BINANCE_API_KEY
        echo    - BINANCE_API_SECRET
        echo    - OPENROUTER_API_KEY
    ) else (
        echo  Warning: src\.env.example not found
    )
)
echo.

echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo INSTALLATION COMPLETE!
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo Next steps:
echo   1. Edit src\.env file with your API keys
echo   2. Run "run.bat" to start using XSignals AI
echo   3. Check README.md for detailed documentation
echo.
echo Get API keys from:
echo   • Binance: https://www.binance.com/en/my/settings/api-management
echo   • OpenRouter: https://openrouter.ai/keys
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
pause
