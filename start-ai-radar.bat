@echo off
title AI Tech Radar (Port 8096)
cd /d "%~dp0"

echo ===================================================
echo   AI Tech Radar - Starting Local Server
echo   URL: http://127.0.0.1:8096
echo ===================================================

if not exist ".env" (
    if exist ".env.example" (
        copy /y ".env.example" ".env" >nul
        echo [INFO] Created initial .env from .env.example
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo [SETUP] Creating Python virtual environment (.venv)...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create .venv. Ensure Python 3.10+ is installed.
        pause
        exit /b 1
    )
    echo [SETUP] Installing dependencies...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

start /b powershell -NoProfile -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8096'"
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8096

if errorlevel 1 (
    echo.
    echo [ERROR] Server exited unexpectedly.
    pause
)
