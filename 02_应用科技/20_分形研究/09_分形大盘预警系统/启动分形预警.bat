@echo off
chcp 936 >nul
title 分形大盘预警系统 - 一键启动
echo ================================================
echo   分形大盘预警系统  Fractal Market Alert
echo   数据模式: 模拟 (接通达信后改 TDX_MODE=tdx)
echo ================================================
echo.
set VENV=C://Users//ThinkPad//.workbuddy//binaries//python//envs//fractal-env//Scripts//python.exe
set APP=%~dp0app.py

if exist "%VENV%" (
    echo [1/2] 使用专用虚拟环境启动...
    start "" "%VENV%" "%APP%"
) else (
    echo [!] 未找到 fractal-env, 尝试系统 Python...
    start "" python "%APP%"
)

echo.
echo [2/2] 浏览器将打开: http://127.0.0.1:5002
timeout /t 2 >nul
start http://127.0.0.1:5002
echo.
echo 服务已在后台启动, 关闭本窗口不影响服务。
pause
