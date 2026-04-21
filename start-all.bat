@echo off
echo Starting Voice AI Agent - Full Stack
echo.
echo This will open two terminal windows:
echo 1. Backend (FastAPI) on http://localhost:8000
echo 2. Frontend (Next.js) on http://localhost:3000
echo.
echo Make sure you have set your GROQ_API_KEY in the .env file!
echo.
pause

start "Voice AI Backend" cmd /k start-backend.bat
timeout /t 5 /nobreak >nul
start "Voice AI Frontend" cmd /k start-frontend.bat

echo.
echo Both servers are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
