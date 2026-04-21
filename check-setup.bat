@echo off
echo ========================================
echo Voice AI Agent - Setup Verification
echo ========================================
echo.

echo Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.11+
    echo Download from: https://www.python.org/downloads/
) else (
    python --version
    echo [OK] Python is installed
)
echo.

echo Checking Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found! Please install Node.js 18+
    echo Download from: https://nodejs.org/
) else (
    node --version
    echo [OK] Node.js is installed
)
echo.

echo Checking npm...
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm not found!
) else (
    npm --version
    echo [OK] npm is installed
)
echo.

echo Checking .env file...
if exist .env (
    echo [OK] .env file exists
    findstr /C:"your_groq_api_key_here" .env >nul
    if %errorlevel% equ 0 (
        echo [WARNING] Please add your actual GROQ_API_KEY to .env file
        echo Get your free API key from: https://console.groq.com
    ) else (
        echo [OK] GROQ_API_KEY appears to be configured
    )
) else (
    echo [ERROR] .env file not found!
    echo Run: copy .env.example .env
)
echo.

echo Checking backend directory...
if exist backend (
    echo [OK] Backend directory exists
    if exist backend\requirements.txt (
        echo [OK] requirements.txt found
    ) else (
        echo [ERROR] requirements.txt not found
    )
) else (
    echo [ERROR] Backend directory not found
)
echo.

echo Checking frontend directory...
if exist frontend\nextjs-ui (
    echo [OK] Frontend directory exists
    if exist frontend\nextjs-ui\package.json (
        echo [OK] package.json found
    ) else (
        echo [ERROR] package.json not found
    )
) else (
    echo [ERROR] Frontend directory not found
)
echo.

echo ========================================
echo Setup Check Complete
echo ========================================
echo.
echo Next steps:
echo 1. Make sure you have added your GROQ_API_KEY to .env
echo 2. Run: start-all.bat
echo 3. Open http://localhost:3000 in your browser
echo.
pause
