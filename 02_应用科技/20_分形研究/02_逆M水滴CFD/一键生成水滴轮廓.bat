@echo off
chcp 65001 >nul
set PY=C:\Users\ThinkPad\.workbuddy\binaries\python\versions\3.13.12\python.exe
echo ========================================
echo   inv-M Droplet Generator
echo ========================================
echo.
echo Generating droplet...
"%PY%" generate_droplet_analytic.py -n 1200 -e 5
if %ERRORLEVEL% neq 0 (
    echo FAILED code %ERRORLEVEL%
    pause
    exit /b 1
)
echo.
echo Done.
dir /b droplet_*.txt droplet_*.csv droplet_*.png 2>nul
pause
