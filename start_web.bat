@echo off
echo ========================================
echo AutoDataPrep - Lancement Application Web
echo ========================================
echo.

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
) else (
    set "PYTHON_CMD=python"
)

echo [1/2] Demarrage de l'API FastAPI...
start "AutoDataPrep API" cmd /k "%PYTHON_CMD% api_server.py"

timeout /t 3 /nobreak >nul

echo [2/2] Demarrage du frontend React...
cd frontend
start "AutoDataPrep Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo Application web demarree!
echo API: http://localhost:8008
echo Frontend: http://localhost:5173
echo Documentation API: http://localhost:8008/docs
echo ========================================
pause
