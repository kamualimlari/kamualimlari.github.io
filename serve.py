#!/usr/bin/env python3
"""Yerelde denemek için: python3 serve.py  →  http://localhost:8000"""
import http.server, socketserver
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store"); super().end_headers()
with socketserver.TCPServer(("", 8000), H) as s:
    print("http://localhost:8000 açık. Durdurmak için Ctrl+C"); s.serve_forever()
