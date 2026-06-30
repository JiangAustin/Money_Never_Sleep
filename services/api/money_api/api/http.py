"""Dependency-free JSON HTTP API boundary."""

from dataclasses import dataclass
import json
from urllib.parse import parse_qs, urlparse

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
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
