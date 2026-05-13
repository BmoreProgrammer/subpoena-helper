@echo off
setlocal enabledelayedexpansion

echo ================================================
echo Subpoena Helper Setup
echo ================================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check Python
echo [1/5] Checking Python...
python --version 2>nul
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+ from python.org
    pause
    exit /b 1
)

REM Download cloudflared if missing
echo.
echo [2/5] Downloading cloudflared (~15MB)...
if not exist "cloudflared.exe" (
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/download/2024.6.1/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe'" 2>nul
    if not exist "cloudflared.exe" (
        echo WARNING: Could not download cloudflared automatically.
        echo Download manually from: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
    ) else (
        echo OK
    )
) else (
    echo cloudflared already present.
)

REM Install dependencies
echo.
echo [3/5] Installing Python dependencies...
python -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)
echo OK

REM Create data dir
echo.
echo [4/5] Creating data directories...
if not exist "data" mkdir data
if not exist "data\pipeline_output" mkdir data\pipeline_output
if not exist "config" mkdir config
echo OK

REM Test Ollama
echo.
echo [5/5] Testing Ollama connection...
python -c "import requests; r=requests.get('http://localhost:11434', timeout=3); print('OK' if r.status_code==200 else 'FAIL')" 2>nul
if errorlevel 1 (
    echo WARNING: Ollama not responding at http://localhost:11434
    echo Make sure Ollama is running on your server.
) else (
    echo OK
)

echo.
echo ================================================
echo Setup complete!
echo.
echo 1. Edit config.py with your Clio credentials
echo 2. Run clio_connect.py to connect to Clio
echo 3. Run SubpoenaHelper.py to start
echo ================================================
pause
