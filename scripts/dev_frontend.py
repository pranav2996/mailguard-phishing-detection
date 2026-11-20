"""Serve the frontend over HTTP for local browser development."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1] / "frontend"
os.chdir(ROOT)

class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

if __name__ == "__main__":
    address = ("127.0.0.1", 5500)
    print(f"Mailguard frontend: http://localhost:{address[1]} (Ctrl+C to stop)")
    ThreadingHTTPServer(address, NoCacheHandler).serve_forever()
