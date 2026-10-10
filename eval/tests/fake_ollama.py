#!/usr/bin/env python3
"""Atrapa API Ollamy do testow eval.py: /api/version, /api/tags, /api/generate.

Odpowiedz zalezy od promptu:
  zawiera "[sleep]" -> czeka 3 s przed odpowiedzia (test timeoutu)
  zawiera "style"   -> "vectorstore"
  inaczej           -> "web_search"
Argument: port (0 = wolny). Wybrany port drukowany w pierwszej linii stdout.
"""
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODELS = [
    {"name": "m-a:1b", "digest": "aaaaaaaaaaaa1111"},
    {"name": "m-b:latest", "digest": "bbbbbbbbbbbb2222"},
]


class Handler(BaseHTTPRequestHandler):
    def _send(self, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/version":
            self._send({"version": "0.0.0-fake"})
        elif self.path == "/api/tags":
            self._send({"models": MODELS})
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(length))
        if self.path != "/api/generate":
            self.send_error(404)
            return
        prompt = req.get("prompt", "")
        if "[sleep]" in prompt:
            time.sleep(3)
        answer = "vectorstore" if "style" in prompt else "web_search"
        try:
            self._send({"model": req["model"], "response": answer, "done": True})
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *args):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(server.server_address[1], flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
