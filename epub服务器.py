import http.server
import socketserver
import webbrowser
import os
import sys
import json
import argparse
from pathlib import Path
from urllib.parse import urlparse, parse_qs

def get_resource_path(relative_path):
    """获取资源的绝对路径，支持开发模式和打包模式"""
    try:
        # 打包后的资源路径
        base_path = sys._MEIPASS
    except Exception:
        # 开发模式的路径
        base_path = Path(__file__).parent
    
    return Path(base_path) / relative_path

def get_config():
    """获取配置文件（打包模式下从资源路径读取）"""
    try:
        if getattr(sys, 'frozen', False):
            # 打包模式：从资源路径读取config.json
            config_path = get_resource_path("config.json")
        else:
            # 开发模式：从当前目录读取config.json
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
            # 开发模式保存到脚本所在目录
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
    """保存历史记录"""
    history = load_history()
    history['last_read'] = {
        'book_path': book_path,
        'cfi': cfi
    }
    save_history(history)

def get_last_position(book_path):
    """获取上次阅读位置"""
    history = load_history()
    if 'last_read' in history:
        last_read = history['last_read']
        if last_read.get('book_path') == book_path:
            return last_read.get('cfi')
    return None

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
            
            # 解析URL参数获取书籍路径
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)
            book_path = (query_params.get('bookPath', [None])[0] or 
                         query_params.get('book', [None])[0] or 
                         query_params.get('b', [None])[0] or 
                         query_params.get('url', [None])[0] or 
                         "epub/book.epub")  # 默认路径
            
            # 获取上次阅读位置
            last_cfi = get_last_position(book_path)
            
            # 注入历史记录恢复代码
            injected_code = f"""
            <script>
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
                        if (path === bookPath) {{
                            options.previousLocationCfi = lastCFI;
                            console.log('设置上次阅读位置:', lastCFI);
                        }}
                        return originalEBookInit(path, options);
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

def main():
    global BOOK_TITLE
    
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
        # 开发模式下，如果也没有提供IP和端口参数，则询问用户
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
        print("正在打开浏览器...")
        print("按 Ctrl+C 停止服务器")
        
        # 自动打开浏览器
        webbrowser.open(f"http://{display_ip}:{port}")
        
        try:
            # 启动服务器
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")
        except Exception as e:
            print(f"\n服务器错误: {e}")

if __name__ == "__main__":
    main()