import os
import sys
import random
import shutil
import argparse
from pathlib import Path

def get_script_dir():
    """获取脚本所在目录"""
    if getattr(sys, 'frozen', False):
        # 打包后的可执行文件所在目录
        return Path(sys.executable).parent
    else:
        # 脚本文件所在目录
        return Path(__file__).parent

def get_book_title_from_file(epub_path):
    """使用ebooklib从电子书文件中获取书名"""
    try:
        from ebooklib import epub
        book = epub.read_epub(epub_path)
        title = book.get_metadata('DC', 'title')
        if title:
            return title[0][0]
        else:
            # 如果没有标题，使用文件名（不含扩展名）
            return Path(epub_path).stem
    except Exception as e:
        print(f"无法从电子书获取标题: {e}")
        return None

def clean_filename(filename):
    """清理文件名中的非法字符"""
    invalid_chars = '<>:"/\\|?*.'
    clean_name = filename
    for char in invalid_chars:
        clean_name = clean_name.replace(char, '_')
    
    # 移除首尾空格和点
    clean_name = clean_name.strip().strip('.')
    return clean_name if clean_name else "unknown_book"

def setup_staging_directory(epub_path, book_title, script_dir):
    """
    设置暂存目录并复制文件
    返回复制后的文件相对路径
    """
    # 清理书名用于文件名
    clean_title = clean_filename(book_title)
    target_filename = f"{clean_title}.epub"
    
    # 检查reader/epub/staging目录是否存在
    reader_staging_dir = script_dir / "reader" / "epub" / "staging"
    
    if reader_staging_dir.exists():
        # 方案1: 复制到reader/epub/staging/
        target_path = reader_staging_dir / target_filename
        try:
            shutil.copy2(epub_path, target_path)
            print(f"已复制电子书到: {target_path}")
            return f"epub/staging/{target_filename}"
        except Exception as e:
            print(f"复制到reader/staging失败: {e}")
            # 如果失败，尝试方案2
            return setup_staging_directory_fallback(epub_path, book_title, script_dir)
    else:
        # 方案2: 复制到脚本目录/staging/并创建符号链接
        return setup_staging_directory_fallback(epub_path, book_title, script_dir)

def setup_staging_directory_fallback(epub_path, book_title, script_dir):
    """备选方案：复制到脚本目录/staging/并创建符号链接"""
    # 清理书名用于文件名
    clean_title = clean_filename(book_title)
    target_filename = f"{clean_title}.epub"
    
    # 创建脚本目录下的staging目录
    script_staging_dir = script_dir / "staging"
    script_staging_dir.mkdir(exist_ok=True)
    
    # 复制文件
    target_path = script_staging_dir / target_filename
    try:
        shutil.copy2(epub_path, target_path)
        print(f"已复制电子书到: {target_path}")
    except Exception as e:
        print(f"复制电子书失败: {e}")
        return None
    
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
        print("请手动创建符号链接或使用其他方法")
    
    return f"epub/staging/{target_filename}"

def generate_batch_script(book_title, epub_path, ip, port, script_dir):
    """生成Windows批处理脚本"""
    clean_title = clean_filename(book_title)
    batch_file = script_dir / f"{clean_title}.bat"
    
    # 获取服务器脚本路径
    server_script = "epub服务器.exe" if getattr(sys, 'frozen', False) else "epub服务器.py"
    
    content = f"""@echo off
chcp 65001 >nul
python --title "{book_title}" --epub "{epub_path}" --ip {ip} --port {port}
"""
    
    try:
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已生成批处理文件: {batch_file}")
        return batch_file
    except Exception as e:
        print(f"生成批处理文件失败: {e}")
        return None

def generate_shell_script(book_title, epub_path, ip, port, script_dir):
    """生成Shell脚本（Unix-like系统）"""
    clean_title = clean_filename(book_title)
    shell_file = script_dir / f"{clean_title}.sh"
    
    # 获取服务器脚本路径
    server_script = "epub服务器" if getattr(sys, 'frozen', False) else "epub服务器.py"
    
    content = f"""#!/bin/bash
python3 "{server_script}" --title "{book_title}" --epub "{epub_path}" --ip {ip} --port {port}
"""
    
    try:
        with open(shell_file, 'w', encoding='utf-8') as f:
            f.write(content)
        # 设置执行权限
        shell_file.chmod(0o755)
        print(f"已生成Shell脚本: {shell_file}")
        return shell_file
    except Exception as e:
        print(f"生成Shell脚本失败: {e}")
        return None

def get_user_input():
    """获取用户输入"""
    script_dir = get_script_dir()
    
    # 获取书名
    book_title = input("请输入书名或拖入epub文件: ").strip().strip('"\'')
    if not book_title:
        print("书名不能为空!")
        return None
    
    # 检查书名是否是文件路径
    epub_path = None
    if os.path.isfile(book_title) and book_title.lower().endswith('.epub'):
        epub_path = book_title
        # 从电子书文件中获取书名
        book_title = get_book_title_from_file(epub_path)
        if book_title is None:
            book_title = input("请输入书名: ").strip()
            if not book_title:
                book_title = Path(epub_path).stem
        print(f"从电子书文件中检测到书名: {book_title}")
    else:
        # 获取电子书路径
        while True:
            epub_path = input("请输入电子书文件路径: ").strip()
            if not epub_path:
                print("电子书路径不能为空!")
                continue
            
            # 处理拖拽文件（可能带有引号）
            epub_path = epub_path.strip('"\'')
            
            if not os.path.isfile(epub_path):
                print(f"文件不存在: {epub_path}")
                continue
            
            if not epub_path.lower().endswith('.epub'):
                print("请提供有效的.epub文件!")
                continue
            
            break
    
    # 获取IP地址
    ip = input("请输入服务器IP（直接回车为localhost）: ").strip()
    if not ip:
        ip = "127.0.0.1"
    
    # 获取端口
    port_input = input("请输入服务器端口（直接回车为随机55000-65535）: ").strip()
    if port_input:
        try:
            port = int(port_input)
        except ValueError:
            print("输入无效，使用随机端口")
            port = random.randint(55000, 65535)
    else:
        port = random.randint(55000, 65535)
    
    # 设置暂存目录并复制文件
    relative_epub_path = setup_staging_directory(epub_path, book_title, script_dir)
    if not relative_epub_path:
        print("设置电子书文件失败!")
        return None
    
    return {
        'book_title': book_title,
        'epub_path': relative_epub_path,
        'ip': ip,
        'port': port,
        'script_dir': script_dir
    }

def main():
    """主函数"""
    
    # 获取用户输入
    params = get_user_input()
    if not params:
        return
    
    # 生成启动脚本
    if os.name == 'nt':  # Windows
        script_file = generate_batch_script(
            params['book_title'], 
            params['epub_path'], 
            params['ip'], 
            params['port'], 
            params['script_dir']
        )
    else:  # Unix-like系统
        script_file = generate_shell_script(
            params['book_title'], 
            params['epub_path'], 
            params['ip'], 
            params['port'], 
            params['script_dir']
        )
    
    if script_file:
        print(f"\n启动脚本已生成: {script_file}")
        print(f"服务器配置: {params['ip']}:{params['port']}")
        print(f"电子书: {params['book_title']}")
        print("\n您可以直接运行此脚本来启动电子书服务器")
    else:
        print("生成启动脚本失败!")

if __name__ == "__main__":
    main()