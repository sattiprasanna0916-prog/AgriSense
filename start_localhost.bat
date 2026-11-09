@echo off
echo ==============================================
echo   Starting AgriSense Localhost Environment
echo ==============================================
echo.

set "BACKEND_DIR=%~dp0"
if exist "%~dp0AgriSense-main\main.py" (
    set "BACKEND_DIR=%~dp0AgriSense-main"
)

echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "AgriSense Backend (FastAPI)" cmd /k "cd /d "%BACKEND_DIR%" && python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Starting React Frontend on http://localhost:5173 ...
start "AgriSense Frontend (Vite)" cmd /k "cd /d "%BACKEND_DIR%\frontend" && npm run dev"

echo.
echo ==============================================
echo   AgriSense is running!
echo   Frontend: http://localhost:5173
echo   Backend:  http://127.0.0.1:8000
echo   API Docs: http://127.0.0.1:8000/docs
echo ==============================================
pause

