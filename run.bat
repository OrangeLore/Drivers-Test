@echo off
REM Driver's Practice Test - portable launcher (Windows). Double-click to run.
cd /d "%~dp0"
if "%AC7_PORT%"=="" set AC7_PORT=5600
echo Starting Driver's Practice Test on http://localhost:%AC7_PORT%
echo (Keep this window open while using the app. Close it to stop the server.)
start "" http://localhost:%AC7_PORT%
python tools\app_server.py %AC7_PORT%
pause
