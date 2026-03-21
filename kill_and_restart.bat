@echo off
echo ========================================
echo Hotel Server - Kill and Restart
echo ========================================
echo.

echo [1/3] Killing all Python processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM python3.11.exe >nul 2>&1
taskkill /F /IM python3.10.exe >nul 2>&1
echo       Done!

echo.
echo [2/3] Waiting for ports to release...
timeout /t 3 /nobreak >nul

echo.
echo [3/3] Starting server...
echo ========================================
echo.

python -u -B run.py
