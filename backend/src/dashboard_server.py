"""Day 8 — Call Analytics Dashboard server.

A deliberately tiny web server (Python stdlib only, no new dependencies)
that serves:
    GET /                -> the dashboard page (dashboard_static/index.html)
    GET /api/summary      -> {total_calls, successful_calls, failed_calls, ...}
    GET /api/calls?limit=N -> recent call history (no sensitive fields)

Data comes straight from calls.db, written to by the agent (src/agent.py)
via src/calls.py every time a real call ends — nothing on this dashboard is
hardcoded or simulated.

Usage:
    uv run python src/dashboard_server.py
    # then open http://localhost:8787

Configure the port with the DASHBOARD_PORT env var.
"""

from __future__ import annotations

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

from calls import get_summary, init_db, list_recent_calls

load_dotenv(".env.local")

logger = logging.getLogger("agent.dashboard")
logging.basicConfig(level=logging.INFO)

_STATIC_DIR = Path(__file__).parent / "dashboard_static"
_INDEX_FILE = _STATIC_DIR / "index.html"

DASHBOARD_PORT = int(os.environ.get("DASHBOARD_PORT", "8787"))


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "PoojaCallDashboard/1.0"

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        logger.info("%s - %s", self.address_string(), format % args)

    def _send_json(self, payload: dict | list, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: int = 200) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            if path == "/" or path == "/index.html":
                html = _INDEX_FILE.read_text(encoding="utf-8")
                self._send_html(html)
                return

            if path == "/api/summary":
                self._send_json(get_summary())
                return

            if path == "/api/calls":
                qs = parse_qs(parsed.query)
                limit = int(qs.get("limit", ["20"])[0])
                self._send_json({"calls": list_recent_calls(limit=limit)})
                return

            self._send_json({"error": "not found"}, status=404)
        except Exception:
            logger.exception("Error handling %s", path)
            self._send_json({"error": "internal error"}, status=500)


def main() -> None:
    init_db()
    server = ThreadingHTTPServer(("0.0.0.0", DASHBOARD_PORT), DashboardHandler)
    logger.info("Call analytics dashboard running at http://localhost:%d", DASHBOARD_PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
