#!/usr/bin/env python3
"""本地静态服务器：把 URL 路径按 UTF-8 解码，修复 Windows 上 Python http.server 对中文路径的处理。

用法：python serve.py [端口，默认 8765]
"""
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote


class UTF8Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Python 把 self.path 留作原始 percent-encoded 字符串。
        # 默认 translate_path 用 surrogatepass 解码，在中文 Windows 上会出错。
        # 这里强制按 UTF-8 解码。
        try:
            decoded = unquote(path, encoding='utf-8', errors='strict')
        except UnicodeDecodeError:
            decoded = unquote(path, encoding='utf-8', errors='replace')
        return super().translate_path(decoded)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    bind = sys.argv[2] if len(sys.argv) > 2 else '0.0.0.0'
    print(f'Serving HTTP on http://{bind}:{port}/  (Ctrl-C to stop)')
    print(f'  本机访问：http://localhost:{port}/')
    # 自动获取本机 IP（用于告诉用户手机/其他设备怎么连）
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
        print(f'  同网段访问：http://{lan_ip}:{port}/')
    except Exception:
        pass
    HTTPServer((bind, port), UTF8Handler).serve_forever()
