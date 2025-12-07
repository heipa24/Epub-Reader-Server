@echo off
chcp 936 >nul
setlocal enabledelayedexpansion
:: 检查Python是否安装及版本
python --version
if errorlevel 1 (
    echo 未检测到Python
    echo 请先安装Python（理论3.6以上就够了,但程序在3.10开发）
    echo 如果已安装Python但没检测则需要将Python添加到PATH（第一次安装则勾选Add Python 3.x to PATH）
    echo 下载地址: https://www.python.org/downloads/
    pause
    start "" "https://www.python.org/downloads/"
    exit /b 1
)

:: 检查Python版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "python_version=%%i"

:: 检查Python是否3.6+
python -c "import sys; exit(0 if sys.version_info >= (3, 6) else 1)" >nul 2>&1
if errorlevel 1 (
    echo Python版本需要3.6或更高版本
    pause
    exit /b 1
)

:: 检查PyInstaller是否安装
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    @echo on
    pip install pyinstaller
    @if errorlevel 1 (
        @echo off
        chcp 65001 >nul
        echo 错误: PyInstaller安装失败
        pause
        exit /b 1
    )
    @echo off
)

:: 检查build.py是否存在
if not exist "build.py" (
    echo 错误: 找不到build.py文件
    pause
    exit /b 1
)

:: 调用Python构建脚本
python build.py

pause