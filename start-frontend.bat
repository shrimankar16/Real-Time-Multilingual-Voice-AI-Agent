@echo off
echo Starting Voice AI Agent Frontend...
echo.

cd frontend\nextjs-ui

if not exist node_modules (
    echo Installing dependencies...
    call npm install
)

echo.
echo Starting Next.js development server on http://localhost:3000
echo Press Ctrl+C to stop the server
echo.

call npm run dev
