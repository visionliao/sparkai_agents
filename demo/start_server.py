import http.server
import socketserver
import webbrowser
import os
import time

# --- 配置区域 ---
# 【修改】更新HTML文件的路径为 index.html
HTML_FILE_PATH = 'index.html'
# 服务器端口
PORT = 3000


# --- 配置结束 ---

def start_server():
    """
    在指定目录下启动一个HTTP服务器，并在浏览器中打开根URL。
    """
    if not os.path.exists(HTML_FILE_PATH):
        print(f"错误: 报告文件 '{HTML_FILE_PATH}' 未找到。")
        print("请先运行 'generate_dashboard.py' 脚本来生成报告。")
        return

    # 服务器应该在 'demo' 目录下运行
    server_dir = os.path.dirname(os.path.abspath(HTML_FILE_PATH))

    Handler = http.server.SimpleHTTPRequestHandler
    original_dir = os.getcwd()
    os.chdir(server_dir)

    try:
        httpd = socketserver.TCPServer(("", PORT), Handler)

        print(f"服务器正在启动...")
        print(f"服务目录: {server_dir}")
        # 【修改】访问地址现在是根URL
        print(f"访问地址: http://localhost:{PORT}/")
        print("(按 Ctrl+C 停止服务器)")

        time.sleep(1)

        # 【修改】在浏览器中直接打开根URL
        url = f"http://localhost:{PORT}/"
        webbrowser.open(url)

        httpd.serve_forever()

    except KeyboardInterrupt:
        print("\n检测到中断信号，正在关闭服务器...")
        httpd.shutdown()
        print("服务器已成功关闭。")
    finally:
        os.chdir(original_dir)


if __name__ == '__main__':
    start_server()