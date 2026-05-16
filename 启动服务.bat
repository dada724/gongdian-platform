@echo off
REM ============================================================
REM  工电中心一体化平台 — Windows 一键启动脚本
REM  使用方法：双击本文件即可启动服务
REM ============================================================

setlocal enabledelayedexpansion

REM --- 自动获取脚本所在目录（支持中文路径）---
set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%backend"

echo ============================================
echo   工电中心一体化平台 - 启动中...
echo ============================================
echo.

REM --- 检查 Python 是否安装 ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    echo        下载地址：https://python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] 检测 Python 环境...
python --version

REM --- 安装依赖 ---
echo.
echo [2/3] 安装 / 更新 Python 依赖...
cd /d "%BACKEND_DIR%"
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)
echo 依赖安装完成。

REM --- 初始化数据库（首次运行）---
echo.
echo [3/3] 初始化数据库...
python -c "import database; database.init_db(); print('数据库就绪')" 2>nul

REM --- 获取本机 IP ---
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4"') do (
    set "IP=%%a"
    goto :found_ip
)
:found_ip
set "IP=%IP: =%"

echo.
echo ============================================
echo   服务启动成功！
echo ============================================
if not "%IP%"=="" (
    echo   本机访问：http://localhost:8000
    echo   局域网访问：http://%IP%:8000
    echo   （手机 / 其他电脑用局域网地址）
) else (
    echo   访问地址：http://localhost:8000
)
echo   按 Ctrl+C 停止服务
echo ============================================
echo.

REM --- 启动 uvicorn（绑定 0.0.0.0 允许局域网访问）---
python -m uvicorn main:app --host 0.0.0.0 --port 8000

pause
