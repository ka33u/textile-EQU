#!/usr/bin/env python3
"""Serve the local exhibit and cache model URLs verified against their file content."""
import hashlib
import re
from functools import lru_cache, partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


@lru_cache(maxsize=64)
def model_digest(path, identity):
    with path.open('rb') as stream:
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
        return digest.hexdigest()


class ExhibitHandler(SimpleHTTPRequestHandler):
    def send_response(self, code, message=None):
        self.response_code = code
        super().send_response(code, message)

    def end_headers(self):
        policy = "no-store, max-age=0"
        url = urlsplit(self.path)
        sha = parse_qs(url.query).get("sha", [""])[0]
        if self.response_code in (200, 304) and url.path.endswith(".glb") and re.fullmatch(r"[0-9a-f]{16}|[0-9a-f]{64}", sha):
            path = Path(self.translate_path(url.path))
            try:
                stat = path.stat()
                if model_digest(path, (stat.st_ino, stat.st_ctime_ns, stat.st_size)).startswith(sha):
                    policy = "public, max-age=31536000, immutable"
            except OSError:
                pass
        elif self.response_code in (200, 304) and url.path.startswith("/vendor/"):
            policy = "no-cache"
        self.send_header("Cache-Control", policy)
        super().end_headers()


if __name__ == "__main__":
    directory = Path(__file__).resolve().parents[1] / "dist"
    handler = partial(ExhibitHandler, directory=str(directory))
    with ThreadingHTTPServer(("127.0.0.1", 4173), handler) as server:
        print("纺织装备工艺与传动交互演示系统已启动：http://127.0.0.1:4173/", flush=True)
        server.serve_forever()
