#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
import json
import random
import zipfile
import xml.etree.ElementTree as ET
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

def get_book_title_from_file(epub_path):
    """使用从电子书文件中获取书名"""
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
                return Path(epub_path).stem
            container_root = ET.fromstring(container_data)
            rootfile = None
            for el in container_root.iter():
                if _local_name(el.tag).lower() == 'rootfile':
                    rootfile = el
                    break
            if rootfile is None:
                return Path(epub_path).stem
            opf_path = rootfile.get('full-path')
            if not opf_path:
                return Path(epub_path).stem
            try:
                opf_data = z.read(opf_path)
            except KeyError:
                names = {n.lower(): n for n in z.namelist()}
                key = opf_path.lower()
                if key in names:
                    opf_data = z.read(names[key])
                else:
                    return Path(epub_path).stem
            opf_root = ET.fromstring(opf_data)
            metadata = None
            for el in opf_root.iter():
                if _local_name(el.tag).lower() == 'metadata':
                    metadata = el
                    break
            if metadata is None:
                return Path(epub_path).stem
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
            return Path(epub_path).stem
    except zipfile.BadZipFile:
        return Path(epub_path).stem

def setup_staging_directory_fallback(script_dir):
    """还原reader/epub/staging/目录"""
    
    # 创建脚本目录下的staging目录
    script_staging_dir = script_dir / "staging"
    script_staging_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建reader/epub/staging目录的符号链接
    reader_staging_dir = script_dir / "reader" / "epub" / "staging"
    reader_staging_dir.parent.mkdir(parents=True, exist_ok=True)
    
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
        print("请手动创建交接点或符号链接")

def get_user_input():
    """获取用户输入"""
    
    # 获取输入（可能是书名或epub文件路径）
    user_input = input("请输入书名或拖入epub文件（建议不同的书使用不同的端口）: ").strip()
    
    # 去除可能的双引号
    user_input = user_input.strip('"')
    
    if not user_input:
        print("错误: 输入不能为空")
        return None
    
    # 检查是否是文件路径
    epub_path = Path(user_input)
    book_title = None
    epub_file_provided = False
    
    if epub_path.exists() and epub_path.suffix.lower() == '.epub':
        epub_file_provided = True
        print(f"检测到epub文件: {epub_path}")
        
        # 检查原book.epub文件大小
        target_file = Path("reader") / "epub" / "book.epub"
        if target_file.exists() and target_file.stat().st_size > 1024:  # 大于1KB
            print("警告: reader/epub/book.epub 非空（大于1KB）")
            confirm = input("确定要继续替换吗？(y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("操作已取消")
                return None
        
        # 从epub文件中获取书名
        book_title = get_book_title_from_file(epub_path)
        print(f"从epub文件中获取的书名: {book_title}")
        
        # 复制epub文件到reader/epub/book.epub
        target_dir = Path("reader") / "epub"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.copy2(epub_path, target_file)
            print(f"已复制epub文件到: {target_file}")
        except Exception as e:
            print(f"错误: 复制epub文件失败: {e}")
            return None
    else:
        # 使用用户输入的书名
        book_title = user_input
    
    if not book_title:
        print("错误: 无法获取有效的书名")
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
        'epub_file_provided': epub_file_provided
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

def check_and_clean_staging_directory():
    """检查并清理staging目录"""
    reparse_point = Path("reader") / "epub" / "staging" / ".reparse_point"
    staging_dir = Path("reader") / "epub" / "staging"
    
    if reparse_point.exists():
        print("检测到.reparse_point文件，正在删除staging目录...")
        try:
            if staging_dir.exists():
                if staging_dir.is_symlink() or staging_dir.is_file():
                    staging_dir.unlink()
                else:
                    shutil.rmtree(staging_dir, ignore_errors=True)
            print("staging目录已删除")
            return True
        except Exception as e:
            print(f"删除staging目录失败: {e}")
            return False
    return False

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
    
    # 删除reader/tmp目录
    tmp_dir = Path("reader") / "tmp"
    if tmp_dir.exists():
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            print("已删除reader/tmp目录")
        except Exception as e:
            print(f"删除reader/tmp目录失败: {e}")
    
    for temp_path in temp_files:
        if Path(temp_path).exists():
            if Path(temp_path).is_file():
                Path(temp_path).unlink()
            else:
                shutil.rmtree(temp_path, ignore_errors=True)
    
    print("清理临时文件完成")

def reset_book_epub():
    """重置book.epub为空文件"""
    target_file = Path("reader") / "epub" / "book.epub"
    if target_file.exists():
        try:
            # 清空文件内容
            with open(target_file, 'wb') as f:
                f.truncate(0)
            print("已重置book.epub为空文件")
        except Exception as e:
            print(f"重置book.epub失败: {e}")

def main():
    """主函数"""
    staging_cleaned = False
    epub_replaced = False
    
    try:
        # 检查环境
        if not check_requirements():
            return 1
        
        # 获取用户输入
        config = get_user_input()
        if not config:
            return 1
        
        # 记录是否替换了epub文件
        epub_replaced = config.get('epub_file_provided', False)
        
        print(f"\n配置信息:")
        print(f"  书名: {config['clean_title']}")
        print(f"  服务器IP: {config['server_ip']}")
        print(f"  服务器端口: {config['server_port']}")
        
        # 检查并清理staging目录
        staging_cleaned = check_and_clean_staging_directory()
        
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
        
        # 如果之前清理了staging目录，现在重新创建符号链接
        if staging_cleaned:
            print("\n重新创建staging目录符号链接...")
            setup_staging_directory_fallback(Path.cwd())
        
        # 如果替换了epub文件，则在最后重置为空文件
        if epub_replaced:
            print("\n重置book.epub文件...")
            reset_book_epub()
        
        # 显示完成信息
        print("\n打包完成!")
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