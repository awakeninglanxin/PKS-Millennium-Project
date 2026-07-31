@echo off
title SEG/IGV Jellium 图表生成
cd /d "%~dp0"

echo ========================================
echo   SEG/IGV Jellium 算法图表一键生成
echo ========================================
echo.

if not exist "%~dp0charts" mkdir "%~dp0charts"

echo [1/5] 量子约束交集分析 (fig1-fig6)...
"C:\Users\ThinkPad\.workbuddy\binaries\python\versions\3.13.12\python.exe" "%~dp0scripts\searl_quantum_vs_truth_table_intersection.py"
if errorlevel 1 echo   Warning: searl_quantum_vs_truth_table_intersection.py 返回错误码
echo    Done.

echo [2/5] 增强算法 vs Searl 对比 (fig7-fig8)...
"C:\Users\ThinkPad\.workbuddy\binaries\python\versions\3.13.12\python.exe" "%~dp0scripts\searl_jellium_layer3_intersection.py"
if errorlevel 1 echo   Warning: searl_jellium_layer3_intersection.py 返回错误码
echo    Done.

echo [3/5] Jellium整除分布 (fig9)...
"C:\Users\ThinkPad\.workbuddy\binaries\python\versions\3.13.12\python.exe" "%~dp0scripts\searl_jellium_layer3_divisibility.py"
if errorlevel 1 echo   Warning: searl_jellium_layer3_divisibility.py 返回错误码
echo    Done.

echo [4/5] 通项公式LCM树 (fig10)...
"C:\Users\ThinkPad\.workbuddy\binaries\python\versions\3.13.12\python.exe" "%~dp0scripts\chart_jellium_tree.py"
if errorlevel 1 echo   Warning: chart_jellium_tree.py 返回错误码
echo    Done.

echo [5/5] 工程价值优化路径 (fig11)...
"C:\Users\ThinkPad\.workbuddy\binaries\python\versions\3.13.12\python.exe" "%~dp0scripts\chart_jellium_engineering.py"
if errorlevel 1 echo   Warning: chart_jellium_engineering.py 返回错误码
echo    Done.

echo.
echo ========================================
echo   生成完成! 图表在 charts\ 文件夹
echo ========================================
echo.
dir /b "%~dp0charts\*.png"
echo.
pause
