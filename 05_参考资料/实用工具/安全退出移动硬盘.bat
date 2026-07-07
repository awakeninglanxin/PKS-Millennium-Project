@echo off
chcp 936 >nul
title 安全退出移动硬盘
setlocal enabledelayedexpansion

echo ============================================
echo   安全退出移动硬盘
echo   自动关闭关联进程 + 安全弹出
echo ============================================
echo.

set PS_FILE=%~dp0安全退出移动硬盘.ps1

if not exist "%PS_FILE%" (
    echo 找不到 .ps1 文件，请确保两个文件在同一目录下。
    pause
    exit /b 1
)

powershell -ExecutionPolicy Bypass -File "%PS_FILE%"

if %errorlevel% neq 0 (
    echo.
    echo 自动弹出失败，请手动操作：
    echo 打开"此电脑" -^> 右键磁盘 -^> 弹出
    pause
)

echo.
echo ============================================
echo   按任意键关闭
echo ============================================
pause >nul
