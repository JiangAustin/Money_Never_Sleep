"""Dependency-free JSON HTTP API boundary."""

from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.parse import parse_qs, urlparse

from money_api.api.v1.router import build_default_analysis_service
from money_api.domains.analysis.service import AnalysisService
from money_api.main import health


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes
    headers: dict[str, str]


class HttpApiApp:
    def __init__(self, service: AnalysisService):
        self.service = service

    def handle(self, method: str, target: str, body: bytes) -> HttpResponse:
        parsed = urlparse(target)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        method = method.upper()

        if method == "OPTIONS":
            return self._json(204, {})
        if method == "GET" and path == "/health":
            return self._json(200, health())
        if method == "POST" and path == "/analysis":
            return self._create_analysis(body)
        if method == "GET" and path == "/reports":
            limit = self._parse_limit(query.get("limit", ["20"])[0])
            return self._json(200, [record.to_dict() for record in self.service.list_reports(limit=limit)])
        if method == "GET" and path.startswith("/reports/"):
            task_id = path.removeprefix("/reports/")
            report = self.service.get_report(task_id)
            if report is None:
                return self._json(404, {"error": "report not found"})
            return self._json(200, report.to_dict())
        if method == "POST" and path.startswith("/reports/") and path.endswith("/backtest"):
            task_id = path.removeprefix("/reports/").removesuffix("/backtest")
            return self._backtest_report(task_id, body)
        return self._json(404, {"error": "not found"})

    def _create_analysis(self, body: bytes) -> HttpResponse:
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "invalid json"})

        symbol = payload.get("symbol")
        message = payload.get("message")
        if not isinstance(symbol, str) or not symbol.strip() or not isinstance(message, str) or not message.strip():
            return self._json(400, {"error": "symbol and message are required"})

        report = self.service.create_single_stock_analysis(symbol, message)
        return self._json(200, report.to_dict())

    def _backtest_report(self, task_id: str, body: bytes) -> HttpResponse:
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "invalid json"})
        prices = payload.get("prices")
        if not isinstance(prices, list):
            return self._json(400, {"error": "prices are required"})
        try:
            from money_api.domains.analysis.contracts import BacktestPricePoint

            result = self.service.backtest_report(task_id, [BacktestPricePoint.from_dict(price) for price in prices])
        except ValueError as exc:
            return self._json(400, {"error": str(exc)})
        if result is None:
            return self._json(404, {"error": "report not found"})
        return self._json(200, result.to_dict())

    def _parse_limit(self, value: str) -> int:
        try:
            limit = int(value)
        except ValueError:
            return 20
        return max(1, min(limit, 100))

    def _json(self, status: int, payload: object) -> HttpResponse:
        return HttpResponse(
            status=status,
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )


def run_http_server(host: str = "127.0.0.1", port: int = 8000, app: HttpApiApp | None = None) -> None:
    api_app = app or HttpApiApp(service=build_default_analysis_service())

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._send(api_app.handle("GET", self.path, b""))

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b""
            self._send(api_app.handle("POST", self.path, body))

        def do_OPTIONS(self) -> None:
            self._send(api_app.handle("OPTIONS", self.path, b""))

        def log_message(self, format: str, *args: object) -> None:
            return

        def _send(self, response: HttpResponse) -> None:
            self.send_response(response.status)
            for name, value in response.headers.items():
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(response.body)))
            self.end_headers()
            self.wfile.write(response.body)

    server = ThreadingHTTPServer((host, port), Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()
