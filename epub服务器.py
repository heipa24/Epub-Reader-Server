import http.server
import socketserver
import webbrowser
import os
import sys
import json
import argparse
import shutil
import threading
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

def get_resource_path(relative_path):
    """获取资源的绝对路径，支持调试模式和打包模式"""
    try:
        # 打包后的资源路径
        base_path = sys._MEIPASS
    except Exception:
        # 调试模式的路径
        base_path = Path(__file__).parent
    
    return Path(base_path) / relative_path

def get_config():
    """获取配置文件（打包模式下从资源路径读取）"""
    try:
        if getattr(sys, 'frozen', False):
            # 打包模式：从资源路径读取config.json
            config_path = get_resource_path("config.json")
        else:
            # 调试模式：从当前目录读取config.json
            config_path = Path("config.json")
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"读取配置文件失败: {e}")
    
    return None

def get_history_dir():
    """获取历史记录目录"""
    try:
        # 打包后保存到exe所在目录
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            # 调试模式保存到脚本所在目录
            base_dir = Path(__file__).parent
    except Exception:
        base_dir = Path.cwd()
    
    history_dir = base_dir / "History"
    history_dir.mkdir(exist_ok=True)
    return history_dir

def clean_filename(filename):
    """清理文件名中的非法字符"""
    invalid_chars = '<>:"/\\|?*.'
    clean_name = filename
    for char in invalid_chars:
        clean_name = clean_name.replace(char, '_')
    
    # 移除首尾空格和点
    clean_name = clean_name.strip().strip('.')
    return clean_name if clean_name else "history"

def get_history_filename():
    """获取历史记录文件名（基于书名）"""
    global BOOK_TITLE
    clean_title = clean_filename(BOOK_TITLE)
    return f"{clean_title}.json"

def load_history():
    """加载历史记录"""
    history_file = get_history_dir() / get_history_filename()
    if history_file.exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_history(history_data):
    """保存历史记录"""
    history_file = get_history_dir() / get_history_filename()
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存历史记录失败: {e}")

def update_history(book_path, cfi):
    """保存历史记录（仅保存CFI信息）"""
    history = load_history()
    history['last_read'] = {
        'cfi': cfi
    }
    save_history(history)

def get_last_position(book_path):
    """获取上次阅读位置（不再验证book_path）"""
    history = load_history()
    if 'last_read' in history:
        return history['last_read'].get('cfi')
    return None

def setup_epub_file(epub_path, book_title, reader_dir):
    """
    设置epub文件：
    - 如果是绝对路径：复制到reader/tmp目录，返回tmp/{book_title}.epub
    - 如果是相对路径：检查文件是否存在，返回原路径
    """
    if not epub_path:
        return "epub/book.epub"  # 默认路径
    
    epub_path = Path(epub_path)
    
    # 如果是绝对路径
    if epub_path.is_absolute():
        # 创建tmp目录
        tmp_dir = reader_dir / "tmp"
        tmp_dir.mkdir(exist_ok=True)
        
        # 生成目标文件名
        clean_title = clean_filename(book_title)
        target_file = tmp_dir / f"{clean_title}.epub"
        
        # 复制文件
        try:
            shutil.copy2(epub_path, target_file)
            print(f"已复制电子书到: {target_file}")
            return f"tmp/{clean_title}.epub"
        except Exception as e:
            print(f"复制电子书失败: {e}")
            return "epub/book.epub"
    
    # 如果是相对路径
    else:
        # 检查文件是否存在
        full_path = reader_dir / epub_path
        if full_path.exists():
            print(f"使用电子书: {full_path}")
            return str(epub_path)
        else:
            print(f"电子书不存在: {full_path}")
            return "epub/book.epub"

def cleanup_temp_dir(reader_dir):
    """清理临时目录"""
    tmp_dir = reader_dir / "tmp"
    if tmp_dir.exists():
        try:
            shutil.rmtree(tmp_dir)
            print(f"已清理临时目录: {tmp_dir}")
        except Exception as e:
            print(f"清理临时目录失败: {e}")
 
    Overkill_count = 0
    while tmp_dir.exists():
        Overkill_count += 1
        print(f"临时目录没删干净, 正在第{Overkill_count}次鞭尸")
        shutil.rmtree(tmp_dir)
        print(f"已成功清理临时目录: {tmp_dir}")

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """处理GET请求，自动注入历史记录恢复代码"""
        if self.path == '/':
            # 重定向到index.html
            self.path = '/index.html'
        
        if self.path.endswith('.html'):
            # 对于HTML文件，注入历史记录恢复代码
            return self.serve_html_with_history()
        else:
            # 其他文件正常处理
            return super().do_GET()
    
    def serve_html_with_history(self):
        """处理HTML文件并注入历史记录恢复代码"""
        try:
            # 获取原始文件路径
            file_path = self.translate_path(self.path)
            if not os.path.isfile(file_path):
                self.send_error(404, "File not found")
                return
            
            # 读取HTML文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用全局的书籍路径
            global CURRENT_BOOK_PATH
            book_path = CURRENT_BOOK_PATH
            
            # 获取上次阅读位置
            last_cfi = get_last_position(book_path)
            
            # 注入历史记录恢复代码和书籍路径覆盖代码
            injected_code = f"""
            <script>
            // 覆盖书籍路径获取函数，强制使用服务器指定的路径
            window.getBookParam = function() {{
                const serverBookPath = {json.dumps(book_path)};
                console.log('使用服务器指定的书籍路径:', serverBookPath);
                return serverBookPath;
            }};
            
            // 历史记录恢复
            document.addEventListener('DOMContentLoaded', function() {{
                const lastCFI = {json.dumps(last_cfi)};
                const bookPath = {json.dumps(book_path)};
                
                console.log('历史记录恢复:', {{ bookPath: bookPath, lastCFI: lastCFI }});
                
                if (lastCFI) {{
                    // 修改ePubReader初始化，直接跳转到上次位置
                    const originalEBookInit = window.ePubReader;
                    window.ePubReader = function(path, options) {{
                        options = options || {{}};
                        // 强制使用服务器指定的路径
                        path = bookPath;
                        if (lastCFI) {{
                            options.previousLocationCfi = lastCFI;
                            console.log('设置上次阅读位置:', lastCFI);
                        }}
                        return originalEBookInit(path, options);
                    }};
                    window.ePubReader.prototype = originalEBookInit.prototype;
                }} else {{
                    // 没有历史记录时，也确保使用正确的路径
                    const originalEBookInit = window.ePubReader;
                    window.ePubReader = function(path, options) {{
                        // 强制使用服务器指定的路径
                        return originalEBookInit(bookPath, options);
                    }};
                    window.ePubReader.prototype = originalEBookInit.prototype;
                }}
                
                // 监听页面变化并保存历史记录
                let currentReader = null;
                const originalOnLoad = window.onload;
                window.onload = function() {{
                    if (originalOnLoad) originalOnLoad();
                    
                    // 等待阅读器初始化
                    setTimeout(() => {{
                        if (window.reader && window.reader.rendition) {{
                            currentReader = window.reader;
                            
                            // 监听页面变化
                            currentReader.rendition.on('relocated', function(location) {{
                                if (location && location.start && location.start.cfi) {{
                                    const cfi = location.start.cfi;
                                    console.log('页面变化，保存历史记录:', cfi);
                                    
                                    // 发送保存请求到后端
                                    fetch('/api/save_history', {{
                                        method: 'POST',
                                        headers: {{
                                            'Content-Type': 'application/json',
                                        }},
                                        body: JSON.stringify({{
                                            book_path: bookPath,
                                            cfi: cfi
                                        }})
                                    }}).catch(err => console.error('保存历史记录失败:', err));
                                }}
                            }});
                        }}
                    }}, 1000);
                }};
            }});
            </script>
            """
            
            # 在</head>标签前注入代码
            if '</head>' in content:
                content = content.replace('</head>', injected_code + '</head>')
            else:
                # 如果没有head标签，在body开始处注入
                content = content.replace('<body>', '<body>' + injected_code)
            
            # 发送修改后的内容
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            
        except Exception as e:
            # 修复HTTP头中的Unicode编码问题
            error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
            self.send_error(500, f"Internal server error: {error_msg}")
    
    def do_POST(self):
        """处理POST请求，用于保存历史记录"""
        if self.path == '/api/save_history':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                book_path = data.get('book_path')
                cfi = data.get('cfi')
                
                if book_path and cfi:
                    update_history(book_path, cfi)
                    print(f"历史记录已保存: {book_path} -> {cfi}")
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success'}).encode('utf-8'))
            except Exception as e:
                self.send_error(500, f"Save history error: {str(e)}")
        else:
            self.send_error(404, "Not found")
    
    def end_headers(self):
        # 添加CORS头信息
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='ePub服务器')
    parser.add_argument('--title', type=str, help='书名')
    parser.add_argument('--epub', type=str, help='ePub电子书路径（绝对路径或相对路径）')
    parser.add_argument('--ip', type=str, help='服务器IP地址')
    parser.add_argument('--port', type=int, help='服务器端口')
    return parser.parse_args()

def is_packaged():
    """检查是否在打包模式下运行"""
    return getattr(sys, 'frozen', False)

def get_user_input():
    """获取用户输入（仅在独立运行时使用）"""
    # 获取服务器IP
    server_ip = input("请输入服务器IP（直接回车为localhost）: ").strip()
    if not server_ip:
        server_ip = "127.0.0.1"
    
    # 获取服务器端口
    server_port_input = input("请输入服务器端口（直接回车为10086）: ").strip()
    if server_port_input:
        try:
            server_port = int(server_port_input)
        except ValueError:
            print("输入无效，使用默认端口10086")
            server_port = 10086
    else:
        server_port = 10086
    
    return server_ip, server_port

def keyboard_listener(httpd, reader_dir):
    """监听键盘输入，ESC键退出"""
    try:
        # 尝试使用msvcrt（Windows）
        import msvcrt
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'\x1b':  # ESC键
                    print("\n收到ESC键，正在退出服务器...")
                    break
            time.sleep(0.1)
    except ImportError:
        # 非Windows系统使用其他方法
        try:
            import termios
            import tty
            import select
            
            # 设置非阻塞输入
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while True:
                    # 检查是否有输入
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        key = sys.stdin.read(1)
                        if key == '\x1b':  # ESC键
                            print("\n收到ESC键，正在退出服务器...")
                            break
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except ImportError:
            # 如果都不支持，使用简单的input方式
            print("按ESC键退出服务器...")
            while True:
                try:
                    # 使用超时输入
                    import select
                    if select.select([sys.stdin], [], [], 1)[0]:
                        line = sys.stdin.readline()
                        if line.strip().lower() in ['esc', 'exit', 'quit']:
                            print("正在退出服务器...")
                            break
                except:
                    # 如果select不支持，使用简单循环
                    time.sleep(1)
    # 关闭服务器
    httpd.shutdown()
    # 清理临时目录
    cleanup_temp_dir(reader_dir)

def main():
    global BOOK_TITLE, CURRENT_BOOK_PATH
    
    # 解析命令行参数
    args = parse_arguments()
    
    # 获取配置（打包模式下从配置文件读取）
    config = None
    if is_packaged():
        config = get_config()
    
    # 设置书名（优先级：命令行参数 > 配置文件 > 默认值）
    if args.title:
        BOOK_TITLE = args.title
        print(f"使用命令行指定的书名: {BOOK_TITLE}")
    elif config and config.get('book_title'):
        BOOK_TITLE = config['book_title']
    elif is_packaged():
        BOOK_TITLE = "history"
    else:
        BOOK_TITLE = "history"
    
    # 获取IP和端口（优先级：命令行参数 > 配置文件 > 默认值）
    if args.ip and args.port:
        ip = args.ip
        port = args.port
        print(f"使用命令行指定的服务器配置: {ip}:{port}")
    elif config and config.get('server_ip') and config.get('server_port'):
        ip = config['server_ip']
        port = config['server_port']
    elif is_packaged():
        ip = "127.0.0.1"
        port = 10086
    else:
        # 调试模式下，如果也没有提供IP和端口参数，则询问用户
        ip, port = get_user_input()
        BOOK_TITLE = "history"
    
    # 获取reader目录路径
    reader_dir = get_resource_path("reader")
    
    # 检查reader目录是否存在
    if not reader_dir.exists():
        print(f"错误: 找不到reader目录: {reader_dir}")
        print("请确保reader目录已正确嵌入")
        input("按回车键退出...")
        sys.exit(1)
    
    # 检查index.html是否存在
    if not (reader_dir / "index.html").exists():
        print(f"错误: 在{reader_dir}中找不到index.html")
        input("按回车键退出...")
        sys.exit(1)
    
    # 处理电子书文件
    epub_path = args.epub if args.epub else (config.get('epub_path') if config else None)
    CURRENT_BOOK_PATH = setup_epub_file(epub_path, BOOK_TITLE, reader_dir)
    
    # 创建历史记录目录
    history_dir = get_history_dir()
    print(f"历史记录目录: {history_dir}")
    print(f"历史记录文件: {get_history_filename()}")
    
    # 切换到reader目录
    os.chdir(reader_dir)
    
    display_ip = 'localhost' if ip == '127.0.0.1' else ip
    
    # 创建HTTP服务器
    with socketserver.TCPServer((ip, port), CORSRequestHandler) as httpd:
        httpd.allow_reuse_address = True
        print(f"服务器启动在 http://{display_ip}:{port}")
        print(f"服务目录: {reader_dir}")
        print(f"当前书籍: {BOOK_TITLE}")
        print(f"电子书路径: {CURRENT_BOOK_PATH}")
        print("正在打开浏览器...")
        print("按 ESC 键优雅地退出服务器")
        
        # 自动打开浏览器
        webbrowser.open(f"http://{display_ip}:{port}")
        
        # 启动键盘监听线程（ESC键退出）
        keyboard_thread = threading.Thread(target=keyboard_listener, args=(httpd, reader_dir), daemon=False)
        keyboard_thread.start()
        
        try:
            # 启动服务器
            httpd.serve_forever()
            print("服务器已优雅地停止")
        except KeyboardInterrupt:
            print("\n收到Ctrl+C，强制停止服务器")
        except Exception as e:
            print(f"\n服务器错误: {e}")

if __name__ == "__main__":
    main()