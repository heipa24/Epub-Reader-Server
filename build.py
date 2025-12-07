#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
import json
import random
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

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

def clean_directories_before_build():
    """打包前清理目录"""
    
    # 删除reader\tmp目录
    tmp_dir = Path("reader") / "tmp"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)
        print("已清理目录: reader/tmp")
    
    # 检查并删除reader\epub\staging目录
    staging_dir = Path("reader") / "epub" / "staging"
    reparse_point = staging_dir / ".reparse_point"
    
    # 记录是否清理了staging目录
    cleaned_staging = False
    
    if reparse_point.exists():
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)
            print("已清理staging重解析点")
            cleaned_staging = True
    
    return cleaned_staging

def get_user_input():
    """获取用户输入"""
    
    # 获取书名或路径
    user_input = input("请输入书名或拖入epub文件（建议不同的书使用不同的端口）: ").strip()
    if not user_input:
        print("错误: 输入不能为空")
        return None
    
    epub_replaced = False
    epub_source_path = None
    
    # 检查输入是否为文件路径
    if Path(user_input).exists() and Path(user_input).is_file():
        epub_source_path = Path(user_input)
        
        # 检查目标epub文件大小
        target_epub = Path("reader") / "epub" / "book.epub"
        if target_epub.exists() and target_epub.stat().st_size > 1024:  # 大于1KB
            response = input("reader/epub/book.epub非空，是否继续? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("操作已取消")
                return None
            
            # 替换epub文件
            try:
                shutil.copy2(epub_source_path, target_epub)
                print(f"已替换epub文件: {target_epub}")
                epub_replaced = True
            except Exception as e:
                print(f"错误: 替换epub文件失败: {e}")
                return None
            
            # 使用 parse_epub_title.py 的 get_epub_title 获取书名
            def get_epub_title(epub_path):
                CONTAINER_PATH = "META-INF/container.xml"
                def _local_name(tag):
                    if tag is None:
                        return ""
                    return tag.split('}')[-1] if '}' in tag else tag
                def _text_of(elem):
                    if elem is None:
                        return ''
                    return ''.join(elem.itertext()).strip()
                try:
                    with zipfile.ZipFile(epub_path, 'r') as z:
                        try:
                            container_data = z.read(CONTAINER_PATH)
                        except KeyError:
                            return None
                        container_root = ET.fromstring(container_data)
                        rootfile = None
                        for el in container_root.iter():
                            if _local_name(el.tag).lower() == 'rootfile':
                                rootfile = el
                                break
                        if rootfile is None:
                            return None
                        opf_path = rootfile.get('full-path')
                        if not opf_path:
                            return None
                        try:
                            opf_data = z.read(opf_path)
                        except KeyError:
                            names = {n.lower(): n for n in z.namelist()}
                            key = opf_path.lower()
                            if key in names:
                                opf_data = z.read(names[key])
                            else:
                                return None
                        opf_root = ET.fromstring(opf_data)
                        metadata = None
                        for el in opf_root.iter():
                            if _local_name(el.tag).lower() == 'metadata':
                                metadata = el
                                break
                        if metadata is None:
                            return None
                        for child in metadata:
                            if _local_name(child.tag).lower() == 'title':
                                text = _text_of(child)
                                if text:
                                    return text
                        for el in opf_root.findall('.//'):
                            if _local_name(el.tag).lower() == 'title':
                                text = _text_of(el)
                                if text:
                                    return text
                        return None
                except zipfile.BadZipFile:
                    return None

            book_title = get_epub_title(str(epub_source_path))
            if not book_title:
                book_title = input("请输入书名: ").strip()
        else:
            book_title = user_input
        
        if not book_title:
            print("错误: 书名不能为空")
            return None
    
    # 获取服务器IP
    server_ip = input("请输入服务器IP（直接回车为127.0.0.1）: ").strip()
    if not server_ip:
        server_ip = "127.0.0.1"
    
    # 获取服务器端口
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
        'server_port': server_port,
        'epub_replaced': epub_replaced,
        'epub_source_path': str(epub_source_path) if epub_source_path else None
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

def setup_staging_symlink():
    """重新创建staging目录的符号链接/交接点"""
    script_dir = Path.cwd()
    script_staging_dir = script_dir / "staging"
    reader_staging_dir = script_dir / "reader" / "epub" / "staging"
    
    # 创建脚本目录下的staging目录（如果不存在）
    script_staging_dir.mkdir(exist_ok=True)
    
    # 创建符号链接/交接点
    try:
        if os.name == 'nt':  # Windows
            # 尝试创建交接点
            import subprocess
            try:
                subprocess.run(['cmd', '/c', 'mklink', '/J', 
                              str(reader_staging_dir), str(script_staging_dir)], 
                            check=True, capture_output=True)
                print(f"已创建交接点: {reader_staging_dir} -> {script_staging_dir}")
            except subprocess.CalledProcessError:
                # 交接点失败，尝试符号链接
                reader_staging_dir.unlink(missing_ok=True)
                os.symlink(script_staging_dir, reader_staging_dir, target_is_directory=True)
                print(f"已创建符号链接: {reader_staging_dir} -> {script_staging_dir}")
        else:  # Unix-like系统
            os.symlink(script_staging_dir, reader_staging_dir, target_is_directory=True)
            print(f"已创建符号链接: {reader_staging_dir} -> {script_staging_dir}")
        
        # 创建.reparse_point文件并检查存在性
        reparse_file = script_staging_dir / ".reparse_point"
        reparse_file.touch()
        check_file = reader_staging_dir / ".reparse_point"
        if check_file.exists():
            print(f"符号链接验证通过: {check_file}")
        else:
            print(f"警告: 符号链接可能未正确工作，未找到 {check_file}")
    except Exception as e:
        print(f"创建符号链接失败: {e}")
        return False
    
    return True

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

def move_and_cleanup(config, cleaned_staging):
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
    
    # 如果替换了epub文件，则在打包完成后将其替换为空文件
    if config.get('epub_replaced', False):
        target_epub = Path("reader") / "epub" / "book.epub"
        try:
            # 创建空文件
            with open(target_epub, 'w') as f:
                f.write('')
            print("已将reader/epub/book.epub替换为空文件")
        except Exception as e:
            print(f"警告: 替换epub文件为空文件失败: {e}")
    
    # 如果之前清理了staging目录，则重新创建符号链接
    if cleaned_staging:
        print("重新创建staging目录符号链接...")
        if setup_staging_symlink():
            print("staging目录符号链接已恢复")
        else:
            print("警告: 重新创建staging目录符号链接失败")
    
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
        
        # 打包前清理目录，并记录是否清理了staging目录
        cleaned_staging = clean_directories_before_build()
        
        # 获取用户输入
        config = get_user_input()
        if not config:
            return 1
        
        print(f"\n配置信息:")
        print(f"  书名: {config['clean_title']}")
        print(f"  服务器IP: {config['server_ip']}")
        print(f"  服务器端口: {config['server_port']}")
        if config.get('epub_source_path'):
            print(f"  EPUB源文件: {config['epub_source_path']}")
        
        # 创建配置文件
        create_config_file(config)
        
        # 生成spec文件
        spec_file = generate_spec_file(config)
        
        # 运行PyInstaller
        if not run_pyinstaller(spec_file):
            return 1
        
        # 移动文件和清理
        if not move_and_cleanup(config, cleaned_staging):
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