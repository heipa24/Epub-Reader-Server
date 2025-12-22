#!/bin/bash

echo "开始处理staging目录..."

# 设置路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
READER_STAGING="$SCRIPT_DIR/reader/epub/staging"
SCRIPT_STAGING="$SCRIPT_DIR/staging"
REPARSE_POINT="$READER_STAGING/.reparse_point"

# 检查并清理staging目录
if [ -f "$REPARSE_POINT" ]; then
    echo "检测到.reparse_point文件，正在删除staging目录..."
    
    if [ -e "$READER_STAGING" ]; then
        if [ -L "$READER_STAGING" ]; then
            echo "删除符号链接: $READER_STAGING"
            rm "$READER_STAGING"
        elif [ -d "$READER_STAGING" ]; then
            echo "删除目录: $READER_STAGING"
            rm -rf "$READER_STAGING"
        else
            echo "删除文件: $READER_STAGING"
            rm -f "$READER_STAGING"
        fi
        echo "staging目录已删除"
    else
        echo "staging目录不存在，无需删除"
    fi
else
    echo "未找到.reparse_point文件，跳过清理"
fi

echo
echo "重新创建staging目录符号链接..."

# 创建脚本目录下的staging目录
if [ ! -d "$SCRIPT_STAGING" ]; then
    mkdir -p "$SCRIPT_STAGING"
    echo "已创建目录: $SCRIPT_STAGING"
fi

# 创建reader/epub目录结构
READER_EPUB="$SCRIPT_DIR/reader/epub"
if [ ! -d "$READER_EPUB" ]; then
    mkdir -p "$READER_EPUB"
fi

# 创建符号链接
if [ ! -e "$READER_STAGING" ]; then
    echo "正在创建符号链接: $READER_STAGING -> $SCRIPT_STAGING"
    
    if ln -s "$SCRIPT_STAGING" "$READER_STAGING" 2>/dev/null; then
        echo "已创建符号链接"
        
        # 创建.reparse_point文件并验证
        touch "$SCRIPT_STAGING/.reparse_point"
        if [ -f "$READER_STAGING/.reparse_point" ]; then
            echo "符号链接验证通过"
        else
            echo "警告: 符号链接可能未正确工作"
        fi
    else
        echo "错误: 无法创建符号链接"
        exit 1
    fi
else
    echo "staging目录已存在，跳过创建"
fi

echo
echo "staging目录处理完成!"