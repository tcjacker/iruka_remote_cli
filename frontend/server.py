#!/usr/bin/env python3
"""
简单的静态文件服务器，用于提供前端界面
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# 设置端口
PORT = 8080

# 获取当前目录
FRONTEND_DIR = Path(__file__).parent

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """支持 CORS 的 HTTP 请求处理器"""
    
    def end_headers(self):
        # 添加 CORS 头部
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()
    
    def do_OPTIONS(self):
        # 处理预检请求
        self.send_response(200)
        self.end_headers()

def main():
    # 切换到前端目录
    os.chdir(FRONTEND_DIR)
    
    print("🚀 启动 Gemini CLI Docker 前端界面")
    print("=" * 50)
    print(f"📁 服务目录: {FRONTEND_DIR}")
    print(f"🌐 访问地址: http://localhost:{PORT}")
    print(f"📋 主页面: http://localhost:{PORT}/index.html")
    print("=" * 50)
    print("💡 提示:")
    print("1. 确保主服务已在 http://localhost:8081 运行")
    print("2. 在浏览器中打开上述地址访问界面")
    print("3. 按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    try:
        # 创建服务器
        with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
            print(f"✅ 服务器已启动在端口 {PORT}")
            print("等待连接...")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n\n🛑 服务器已停止")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ 端口 {PORT} 已被占用，请尝试其他端口")
            print(f"或者使用命令: python server.py --port 8081")
        else:
            print(f"❌ 启动服务器失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 服务器错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
