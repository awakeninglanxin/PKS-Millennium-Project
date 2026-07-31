@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ═══════════════════════════════════════
echo   逆M集水滴轮廓批量生成器
echo   4个标准Farey泡: 1/3 2/5 3/8 1/2
echo ═══════════════════════════════════════
echo.

set PY=python

echo [1/4] p/q=1/3 (经典水滴) ...
%PY% generate_droplet.py -p 1 -q 3 -r 2000 -s 3.0

echo.
echo [2/4] p/q=2/5 (稍扁水滴) ...
%PY% generate_droplet.py -p 2 -q 5 -r 2000 -s 3.0

echo.
echo [3/4] p/q=3/8 (颀长水滴) ...
%PY% generate_droplet.py -p 3 -q 8 -r 2000 -s 3.5

echo.
echo [4/4] p/q=1/2 (最经典最大水滴) ...
%PY% generate_droplet.py -p 1 -q 2 -r 2000 -w 0.25 -s 4.0

echo.
echo ═══════════════════════════════════════
echo   全部完成! 输出文件:
dir /b droplet_*.txt droplet_*.csv 2>nul
echo ═══════════════════════════════════════
pause
