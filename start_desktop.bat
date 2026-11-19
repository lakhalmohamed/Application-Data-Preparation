@echo off
echo ========================================
echo AutoDataPrep - Lancement Application Bureau
echo ========================================
echo.

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
) else (
    set "PYTHON_CMD=python"
)

%PYTHON_CMD% main.py

pause
