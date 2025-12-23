@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

rem if "%~1"=="SPECIAL_PARAM" (
rem 	goto SPECIAL_SECTION
rem )

:: 创建脚本目录下的staging目录
if not exist "%~dp0staging" (
    echo 不存在目录"%~dp0staging"无需修复
    pause
    exit /b
)

:: 检查并清理staging目录
if exist "%~dp0reader\epub\staging\.reparse_point" (
    echo 检测到%~dp0reader\epub\staging\.reparse_point文件，正在删除%~dp0reader\epub\staging目录...
    rmdir /s /q "%~dp0reader\epub\staging" 2>nul
) if exist "%~dp0staging\.reparse_point"(
    echo 检测到%~dp0staging\.reparse_point文件，正在删除%~dp0reader\epub\staging目录...
	rmdir /s /q "%~dp0reader\epub\staging" 2>nul
) else (
    echo 未找到.reparse_point文件，无需修复
    pause
    exit /b
)

:: 重新创建staging目录符号链接
echo.
echo 重新创建staging目录符号链接...

:: 创建符号链接或交接点
if not exist "%~dp0reader\epub\staging" (
    echo 正在创建符号链接: %~dp0reader\epub\staging -> %~dp0staging
    
    :: 尝试创建交接点
    mklink /J "%~dp0reader\epub\staging" "%~dp0staging" >nul 2>&1
    if !errorlevel! equ 0 (
        echo 已创建交接点
    ) else (
        :: 交接点失败，尝试符号链接
        echo 交接点创建失败，尝试符号链接...
        rem :SPECIAL_SECTION
        rem net session >nul 2>&1
        rem if !errorLevel! neq 0 (
        rem :: 不是管理员，重新启动自己
        rem echo 请求管理员权限...
        rem powershell -Command "Start-Process '%~s0' -ArgumentList 'SPECIAL_PARAM' -Verb RunAs"
        rem exit /b
        rem )
        rem mklink /D "%~dp0reader\epub\staging" "%~dp0staging" >nul 2>&1
        powershell -Command "Start-Process PowerShell -ArgumentList '-Command New-Item -ItemType SymbolicLink -Path \"%~dp0reader\epub\staging\" -Target \"%~dp0staging\"' -Verb RunAs" -Wait
        if !errorlevel! equ 0 (
            echo 已创建符号链接
        ) else (
            echo 错误: 无法创建符号链接或交接点
            pause
            exit /b
        )
    )
    
    :: 创建.reparse_point文件并验证
    echo. > "%~dp0staging\.reparse_point"
    if exist "%~dp0reader\epub\staging\.reparse_point" (
        echo 重解析点验证通过
    ) else (
        echo 警告: 重解析点可能未正确工作
    )
) else (
    echo staging目录已存在，跳过创建
)

echo.
echo staging目录处理完成!
pause
exit /b