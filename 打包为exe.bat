@echo off
chcp 65001 >nul

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未检测到Python，请先安装Python 3.6+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查PyInstaller是否安装
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 正在安装PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo 错误: PyInstaller安装失败
        pause
        exit /b 1
    )
)

:: 检查reader目录是否存在
if not exist "reader" (
    echo 错误: 找不到reader目录
    echo 请确保reader目录与bat文件在同一目录下
    pause
    exit /b 1
)

:: 检查index.html是否存在
if not exist "reader\index.html" (
    echo 错误: reader目录中没有index.html文件
    pause
    exit /b 1
)

:: 检查服务器.py是否存在
if not exist "epub服务器.py" (
    echo 错误: 找不到epub服务器.py文件
    pause
    exit /b 1
)


:: 开始打包
@echo on
pyinstaller build.spec

@if errorlevel 1 (goto echo)

@echo off


:: 移动exe文件到当前目录
if exist "dist\epub服务器.exe" (
    echo 移动可执行文件...
    move "dist\epub服务器.exe" "epub服务器.exe" >nul
    echo 打包完成! 可执行文件已生成: epub服务器.exe
)

:cleanup
:: 清理临时文件
echo 清理临时文件...
if exist "build" rmdir /s /q "build" >nul 2>&1
if exist "dist" rmdir /s /q "dist" >nul 2>&1
if exist "__pycache__" rmdir /s /q "__pycache__" >nul 2>&1

pause
exit /b

:echo
@echo off
echo 错误: 打包失败
goto cleanup
