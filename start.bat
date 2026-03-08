@echo off
REM PAA Extractor — One-click startup script for Windows
REM This starts the server AND creates a public tunnel URL

echo.
echo   =======================================
echo     PAA Extractor — Starting Up
echo   =======================================
echo.

REM Kill any existing instances
echo   [0] Cleaning up old processes...
taskkill /F /IM "uvicorn.exe" >nul 2>&1
taskkill /F /IM "ngrok.exe" >nul 2>&1
timeout /t 1 >nul

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start the PAA server in a new minimized window
echo   [1/2] Starting PAA server on http://localhost:8000 ...
start /MIN "PAA-Server" cmd /c "call venv\Scripts\activate.bat && set HEADLESS=false && uvicorn main:app --port 8000"
timeout /t 3 >nul
echo   Server started!
echo.

REM Start ngrok and look for URL
echo   [2/2] Creating public tunnel (using ngrok)...
echo   (Wait for the ngrok-free.app URL to appear)
echo.

ngrok http 8000

echo.
echo   =======================================
echo     Look for the ngrok-free.app URL above
echo     and copy it for n8n!
echo   =======================================
echo.
echo   Add /api/paa at the end of the URL
echo   Example: https://your-url.ngrok-free.app/api/paa
echo.
echo   NOTE: Ngrok provides a permanent URL!
echo   You only need to configure this in n8n once.
echo.
echo   Press Ctrl+C to stop the tunnel.
echo   Close this window to stop everything.
pause
