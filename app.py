"""Web server for the IoT simulation visualization."""

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from main import build_demo


ROOT = Path(__file__).parent
STATIC_DIR = ROOT / "static"


class DemoHandler(SimpleHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - stdlib method name
        parsed = urlparse(self.path)
        if parsed.path == "/api/demo":
            params = parse_qs(parsed.query)
            agent_count = clamp_int(params.get("agents", ["8"])[0], 4, 14)
            probability = clamp_float(params.get("probability", ["0.28"])[0], 0.0, 1.0)
            seed = clamp_int(params.get("seed", ["7"])[0], 1, 99999)
            self.send_json(build_demo(agent_count, probability, seed))
            return

        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def translate_path(self, path):
        return str(STATIC_DIR / path.lstrip("/"))

    def send_json(self, payload):
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def clamp_int(value, low, high):
    try:
        return max(low, min(high, int(value)))
    except ValueError:
        return low


def clamp_float(value, low, high):
    try:
        return max(low, min(high, float(value)))
    except ValueError:
        return low


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 8000), DemoHandler)
    print("IoT visualization demo running at http://127.0.0.1:8000")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
