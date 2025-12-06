#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
import json
import random
from pathlib import Path

def check_requirements():
    """检查必要的文件和目录是否存在"""
    
    # 检查reader目录
    if not Path("reader").exists():
        print("错误: 找不到reader目录")
        print("请确保reader目录与脚本在同一目录下")
        return False
    
    # 检查index.html
    if not (Path("reader") / "index.html").exists():
        print("错误: reader目录中没有index.html文件")
        return False
    
    # 检查服务器.py
    if not Path("epub服务器.py").exists():
        print("错误: 找不到epub服务器.py文件")
        return False
    
    return True

def get_user_input():
    """获取用户输入"""
    
    # 获取书名
    book_title = input("请输入书名（建议不同的书使用不同的端口）: ").strip()
    if not book_title:
        print("错误: 书名不能为空")
        return None
    
    # 获取服务器IP
    server_ip = input("请输入服务器IP（直接回车为127.0.0.1）: ").strip()
    if not server_ip:
        server_ip = "127.0.0.1"
    
    # 获取服务器端口（修改部分）
    server_port_input = input("请输入服务器端口（直接回车端口在55000-65535之间随机）: ").strip()
    if server_port_input:
        try:
            server_port = int(server_port_input)
            # 验证端口范围
            if server_port < 1 or server_port > 65535:
                print("错误: 端口必须在1-65535范围内")
                return None
        except ValueError:
            print("错误: 端口必须是数字")
            return None
    else:
        # 在55000-65535之间随机选择一个端口
        server_port = random.randint(55000, 65535)
        print(f"已随机选择端口: {server_port}")
    
    # 清理书名中的非法字符
    clean_title = clean_filename(book_title)
    if not clean_title:
        print("错误: 书名不能只包含非法字符")
        return None
    
    return {
        'book_title': book_title,
        'clean_title': clean_title,
        'server_ip': server_ip,
        'server_port': server_port
    }

def clean_filename(filename):
    """清理文件名中的非法字符"""
    invalid_chars = '<>:"/\\|?*.'
    clean_name = filename
    for char in invalid_chars:
        clean_name = clean_name.replace(char, '_')
    
    # 移除首尾空格和点
    clean_name = clean_name.strip().strip('.')
    return clean_name

def generate_spec_file(config):
    """生成PyInstaller的spec文件"""
    clean_title = config['clean_title']
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['epub服务器.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('reader', 'reader'),
        ('config.json', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{clean_title}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codepage='utf8',
)
"""
    
    spec_file = "temp_build.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    return spec_file

def create_config_file(config):
    """创建配置文件"""
    config_data = {
        'book_title': config['clean_title'],
        'server_ip': config['server_ip'],
        'server_port': config['server_port']
    }
    
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)
    
    print("创建配置文件: config.json")

def run_pyinstaller(spec_file):
    """运行PyInstaller进行打包"""
    print(f"\n开始打包，使用配置文件: {spec_file}")
    
    try:
        result = subprocess.run([
            'pyinstaller', spec_file, '--noconfirm'
        ], check=True, capture_output=True, text=True)
        
        print("PyInstaller打包完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误: PyInstaller打包失败")
        print(f"错误信息: {e.stderr}")
        return False
    except Exception as e:
        print(f"错误: 执行PyInstaller时发生异常: {e}")
        return False

def move_and_cleanup(config):
    """移动生成的文件并清理临时文件"""
    clean_title = config['clean_title']
    
    print("\n处理生成的文件...")
    
    # 移动exe文件到当前目录
    exe_source = Path("dist") / f"{clean_title}.exe"
    if exe_source.exists():
        shutil.move(str(exe_source), f"{clean_title}.exe")
        print(f"移动可执行文件: {clean_title}.exe")
    else:
        print(f"警告: 找不到生成的可执行文件: {exe_source}")
        return False
    
    # 清理临时文件
    cleanup_temp_files()
    
    return True

def cleanup_temp_files():
    """清理临时文件"""
    temp_files = [
        "temp_build.spec",
        "build",
        "dist",
        "__pycache__",
        "config.json"
    ]
    
    for temp_path in temp_files:
        if Path(temp_path).exists():
            if Path(temp_path).is_file():
                Path(temp_path).unlink()
            else:
                shutil.rmtree(temp_path, ignore_errors=True)
    
    print("清理临时文件完成")

def main():
    """主函数"""
    try:
        # 检查环境
        if not check_requirements():
            return 1
        
        # 获取用户输入
        config = get_user_input()
        if not config:
            return 1
        
        print(f"\n配置信息:")
        print(f"  书名: {config['clean_title']}")
        print(f"  服务器IP: {config['server_ip']}")
        print(f"  服务器端口: {config['server_port']}")
        
        # 创建配置文件
        create_config_file(config)
        
        # 生成spec文件
        spec_file = generate_spec_file(config)
        
        # 运行PyInstaller
        if not run_pyinstaller(spec_file):
            return 1
        
        # 移动文件和清理
        if not move_and_cleanup(config):
            return 1
        
        # 显示完成信息
        print("打包完成!")
        print(f"可执行文件: {config['clean_title']}.exe")
        print(f"历史记录文件: History/{config['clean_title']}.json")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n用户中断打包过程")
        cleanup_temp_files()
        return 1
    except Exception as e:
        print(f"\n错误: 打包过程中发生异常: {e}")
        cleanup_temp_files()
        return 1

if __name__ == "__main__":
    sys.exit(main())