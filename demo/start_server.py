import http.server
import socketserver
import webbrowser
import os
import time

# --- 配置区域 ---
# 需要启动服务的HTML文件的相对路径
HTML_FILE_PATH = 'dashboard.html'
# 服务器端口
PORT = 3006


# --- 配置结束 ---

def start_server():
    """
    在指定目录下启动一个HTTP服务器，并在浏览器中打开指定的HTML文件。
    """
    # 检查HTML文件是否存在，如果不存在则提示用户先生成报告
    if not os.path.exists(HTML_FILE_PATH):
        print(f"错误: 报告文件 '{HTML_FILE_PATH}' 未找到。")
        print("请先运行 'generate_dashboard.py' 脚本来生成报告。")
        return

    # 确定服务器应该在哪个目录下运行
    # 例如，如果路径是 'demo/dashboard.html'，服务器就在 'demo' 目录下运行
    server_dir = os.path.dirname(os.path.abspath(HTML_FILE_PATH))
    html_filename = os.path.basename(HTML_FILE_PATH)

    # 定义一个处理HTTP请求的Handler
    Handler = http.server.SimpleHTTPRequestHandler

    # 记录当前目录，以便结束后能切回去
    original_dir = os.getcwd()
    # 切换到目标目录来启动服务器
    os.chdir(server_dir)

    try:
        # 创建并配置服务器
        httpd = socketserver.TCPServer(("", PORT), Handler)

        print(f"服务器正在启动...")
        print(f"服务目录: {server_dir}")
        print(f"访问地址: http://localhost:{PORT}/{html_filename}")
        print("(按 Ctrl+C 停止服务器)")

        # 延迟一秒，确保服务器完全启动后再打开浏览器
        time.sleep(1)

        # 构建URL并在浏览器中打开
        url = f"http://localhost:{PORT}/{html_filename}"
        webbrowser.open(url)

        # 启动服务器，它会一直运行直到被手动停止
        httpd.serve_forever()

    except KeyboardInterrupt:
        # 当用户按下 Ctrl+C 时，优雅地关闭服务器
        print("\n检测到中断信号，正在关闭服务器...")
        httpd.shutdown()
        print("服务器已成功关闭。")
    finally:
        # 无论如何，最后都要切换回原始目录
        os.chdir(original_dir)


if __name__ == '__main__':
    start_server()