import json

from money_api.api.http import HttpApiApp
from money_api.api.v1.router import build_default_analysis_service
from money_api.domains.analysis.report_repository import InMemoryAnalysisReportRepository


def build_app() -> HttpApiApp:
    service = build_default_analysis_service(report_repository=InMemoryAnalysisReportRepository())
    return HttpApiApp(service=service)


def decode(response):
    return json.loads(response.body.decode("utf-8"))


def test_http_health() -> None:
    response = build_app().handle("GET", "/health", b"")

    assert response.status == 200
    assert decode(response)["status"] == "ok"


def test_http_create_analysis_and_get_report() -> None:
    app = build_app()
    response = app.handle("POST", "/analysis", json.dumps({"symbol": "贵州茅台", "message": "请全面分析"}).encode("utf-8"))

    payload = decode(response)
    report = decode(app.handle("GET", f"/reports/{payload['task_id']}", b""))

    assert response.status == 200
    assert payload["stock"]["code"] == "600519"
    assert report["task_id"] == payload["task_id"]


def test_http_list_reports() -> None:
    app = build_app()
    app.handle("POST", "/analysis", json.dumps({"symbol": "贵州茅台", "message": "请全面分析"}).encode("utf-8"))

    response = app.handle("GET", "/reports?limit=5", b"")

    assert response.status == 200
    assert decode(response)[0]["stock"]["code"] == "600519"


def test_http_returns_400_for_invalid_analysis_payload() -> None:
    response = build_app().handle("POST", "/analysis", b"{}")

    assert response.status == 400
    assert decode(response)["error"] == "symbol and message are required"


def test_http_returns_404_for_missing_report() -> None:
    response = build_app().handle("GET", "/reports/missing", b"")

    assert response.status == 404
