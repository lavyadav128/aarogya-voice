@echo off
title AarogyaVoice - Bolna Voice AI Clinical Platform
echo ======================================================================
echo    AAROGYAVOICE - AUTONOMOUS CLINICAL VOICE RECEPTIONIST
echo    Symphony Buildathon by Bolna (YC F25)
echo    Developer: Lav Yadav (github.com/lavyadav182)
echo ======================================================================
echo.

cd /d "%~dp0"

echo [1/3] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not found in PATH!
    pause
    exit /b 1
)

echo [2/3] Initializing clinic database and seed records...
python -c "import backend.main; print('[OK] Database initialized successfully.')"

echo [3/3] Launching AarogyaVoice server at http://localhost:8000 ...
echo.
echo Opening browser dashboard...
start http://localhost:8000

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
pause
