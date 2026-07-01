"""Dependency-free JSON HTTP API boundary."""

from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.parse import parse_qs, urlparse

from money_api.api.v1.router import build_runtime_analysis_service
from money_api.domains.analysis.contracts import BacktestOptions
from money_api.domains.analysis.service import AnalysisService
from money_api.domains.analysis.task_queue import InMemoryAnalysisTaskQueue
from money_api.domains.market_data.sina_kline import SinaKLineProvider
from money_api.main import health


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes
    headers: dict[str, str]


class HttpApiApp:
    def __init__(self, service: AnalysisService, price_providers: dict[str, object] | None = None, task_queue: InMemoryAnalysisTaskQueue | None = None):
        self.service = service
        self.price_providers = price_providers or {"sina": SinaKLineProvider()}
        self.task_queue = task_queue or InMemoryAnalysisTaskQueue(service=service)

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
        if method == "POST" and path == "/tasks/analysis":
            return self._create_analysis_task(body)
        if method == "GET" and path == "/reports":
            limit = self._parse_limit(query.get("limit", ["20"])[0])
            return self._json(200, [record.to_dict() for record in self.service.list_reports(limit=limit)])
        if method == "GET" and path.startswith("/tasks/"):
            task_id = path.removeprefix("/tasks/")
            task = self.task_queue.get_task(task_id)
            if task is None:
                return self._json(404, {"error": "task not found"})
            return self._json(200, task.to_dict())
        if method == "GET" and path.startswith("/reports/"):
            task_id = path.removeprefix("/reports/")
            report = self.service.get_report(task_id)
            if report is None:
                return self._json(404, {"error": "report not found"})
            return self._json(200, report.to_dict())
        if method == "POST" and path.startswith("/reports/") and path.endswith("/backtest"):
            task_id = path.removeprefix("/reports/").removesuffix("/backtest")
            return self._backtest_report(task_id, body)
        if method == "POST" and path == "/portfolio/risk-budget":
            return self._portfolio_risk_budget(body)
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

    def _create_analysis_task(self, body: bytes) -> HttpResponse:
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "invalid json"})

        symbol = payload.get("symbol")
        message = payload.get("message")
        if not isinstance(symbol, str) or not symbol.strip() or not isinstance(message, str) or not message.strip():
            return self._json(400, {"error": "symbol and message are required"})

        task = self.task_queue.create_analysis_task(symbol, message)
        return self._json(202, task.to_dict())

    def _backtest_report(self, task_id: str, body: bytes) -> HttpResponse:
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "invalid json"})
        prices = payload.get("prices")
        source = payload.get("source")
        limit = self._parse_limit(str(payload.get("limit", "60")))
        options = BacktestOptions.from_dict(payload.get("options"))
        try:
            if source == "sina":
                result = self.service.backtest_report_from_provider(task_id, self.price_providers["sina"], limit=limit, options=options)
            else:
                if not isinstance(prices, list):
                    return self._json(400, {"error": "prices are required"})
                from money_api.domains.analysis.contracts import BacktestPricePoint

                result = self.service.backtest_report(task_id, [BacktestPricePoint.from_dict(price) for price in prices], options=options)
        except ValueError as exc:
            return self._json(400, {"error": str(exc)})
        if result is None:
            return self._json(404, {"error": "report not found"})
        return self._json(200, result.to_dict())

    def _portfolio_risk_budget(self, body: bytes) -> HttpResponse:
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "invalid json"})
        task_ids = payload.get("task_ids")
        if task_ids is not None and not isinstance(task_ids, list):
            return self._json(400, {"error": "task_ids must be a list"})
        limit = self._parse_limit(str(payload.get("limit", "20")))
        budget = self.service.build_portfolio_risk_budget(
            task_ids=[str(task_id) for task_id in task_ids] if task_ids is not None else None,
            limit=limit,
        )
        return self._json(200, budget.to_dict())

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
    api_app = app or HttpApiApp(service=build_runtime_analysis_service())

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
