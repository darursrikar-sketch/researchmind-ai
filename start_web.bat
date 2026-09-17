@echo off
title ResearchMind AI Dashboard
cd /d "%~dp0"

echo =========================================================
echo   Starting ResearchMind AI - Academic Paper Agent
echo =========================================================
echo.
echo Opening browser at http://localhost:5000 ...

start timeout /t 2 /nobreak >nul & start http://localhost:5000
python run_web.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred while running ResearchMind AI.
    pause
)

