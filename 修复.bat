@echo off
chcp 65001 >nul
 
:: 创建脚本目录下的staging目录
if not exist "%~dp0staging" (
    echo 不存在目录"%~dp0staging"无需修复
    pause
    exit /b
)

:: 检查并清理staging目录
if exist "%~dp0reader\epub\staging\.reparse_point" (
    echo 检测到.reparse_point文件，正在删除staging目录...
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
        mklink /D "%~dp0reader\epub\staging" "%~dp0staging" >nul 2>&1
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