import json

from money_api.api.http import HttpApiApp
from money_api.api.v1.router import build_default_analysis_service
from money_api.domains.analysis.contracts import AnalysisStatus, BacktestPricePoint
from money_api.domains.analysis.report_repository import InMemoryAnalysisReportRepository
from money_api.domains.analysis.task_queue import AnalysisTaskRecord, InMemoryAnalysisTaskQueue, InMemoryAnalysisTaskRepository
from money_api.domains.market_data.provider_results import ProviderResult
from money_api.main import run_http_server


class FakePriceProvider:
    def get_price_series(self, stock, limit=60):
        return ProviderResult(
            kind="price_series",
            source="fake",
            ok=True,
            data=[BacktestPricePoint(date="2026-07-01", close=100.0), BacktestPricePoint(date="2026-07-02", close=116.0)],
        )


def build_app() -> HttpApiApp:
    service = build_default_analysis_service(report_repository=InMemoryAnalysisReportRepository())
    return HttpApiApp(
        service=service,
        price_providers={"sina": FakePriceProvider()},
        task_queue=InMemoryAnalysisTaskQueue(
            service=service,
            repository=InMemoryAnalysisTaskRepository(),
            executor=lambda operation: operation(),
        ),
    )


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


def test_http_create_analysis_task_and_poll_status() -> None:
    app = build_app()

    response = app.handle("POST", "/tasks/analysis", json.dumps({"symbol": "贵州茅台", "message": "请全面分析"}).encode("utf-8"))

    assert response.status == 202
    task = decode(response)
    assert task["status"] in {"queued", "quick_screening", "deep_analysis", "report_ready"}

    polled = decode(app.handle("GET", f"/tasks/{task['task_id']}", b""))

    assert polled["task_id"] == task["task_id"]
    assert polled["status"] in {"queued", "quick_screening", "deep_analysis", "report_ready"}


def test_http_list_tasks() -> None:
    app = build_app()
    app.handle("POST", "/tasks/analysis", json.dumps({"symbol": "贵州茅台", "message": "请全面分析"}).encode("utf-8"))

    response = app.handle("GET", "/tasks?limit=5", b"")

    assert response.status == 200
    payload = decode(response)
    assert payload
    assert payload[0]["symbol"] == "贵州茅台"


def test_http_create_analysis_task_accepts_timeout() -> None:
    app = build_app()

    response = app.handle(
        "POST",
        "/tasks/analysis",
        json.dumps({"symbol": "贵州茅台", "message": "请全面分析", "timeout_s": 12}).encode("utf-8"),
    )

    assert response.status == 202
    assert decode(response)["timeout_s"] == 12


def test_http_get_task_marks_timeout() -> None:
    service = build_default_analysis_service(report_repository=InMemoryAnalysisReportRepository())
    repository = InMemoryAnalysisTaskRepository()
    queue = InMemoryAnalysisTaskQueue(service=service, repository=repository, executor=lambda operation: None)
    timed_out = AnalysisTaskRecord(
        task_id="task-timeout",
        symbol="600519",
        message="请全面分析",
        status=AnalysisStatus.DEEP_ANALYSIS.value,
        created_at="2026-07-01T00:00:00+00:00",
        updated_at="2026-07-01T00:00:00+00:00",
        started_at="2026-07-01T00:00:00+00:00",
        timeout_s=1,
    )
    repository.save(timed_out)
    queue._records[timed_out.task_id] = timed_out
    queue._now = lambda: "2026-07-01T00:00:05+00:00"  # type: ignore[attr-defined]
    app = HttpApiApp(
        service=service,
        price_providers={"sina": FakePriceProvider()},
        task_queue=queue,
    )

    response = app.handle("GET", "/tasks/task-timeout", b"")

    assert response.status == 200
    payload = decode(response)
    assert payload["status"] == AnalysisStatus.FAILED.value
    assert payload["error"] == "task timed out after 1s"


def test_http_task_returns_400_for_invalid_payload() -> None:
    response = build_app().handle("POST", "/tasks/analysis", b"{}")

    assert response.status == 400
    assert decode(response)["error"] == "symbol and message are required"


def test_http_returns_400_for_invalid_analysis_payload() -> None:
    response = build_app().handle("POST", "/analysis", b"{}")

    assert response.status == 400
    assert decode(response)["error"] == "symbol and message are required"


def test_http_returns_404_for_missing_report() -> None:
    response = build_app().handle("GET", "/reports/missing", b"")

    assert response.status == 404


def test_http_returns_404_for_missing_task() -> None:
    response = build_app().handle("GET", "/tasks/missing", b"")

    assert response.status == 404


def test_http_can_cancel_task() -> None:
    service = build_default_analysis_service(report_repository=InMemoryAnalysisReportRepository())
    repository = InMemoryAnalysisTaskRepository()
    app = HttpApiApp(
        service=service,
        price_providers={"sina": FakePriceProvider()},
        task_queue=InMemoryAnalysisTaskQueue(service=service, repository=repository, executor=lambda operation: None),
    )
    task = decode(app.handle("POST", "/tasks/analysis", json.dumps({"symbol": "贵州茅台", "message": "请全面分析"}).encode("utf-8")))

    response = app.handle("POST", f"/tasks/{task['task_id']}/cancel", b"")

    assert response.status == 200
    assert decode(response)["status"] == "cancelled"


def test_http_can_retry_failed_task() -> None:
    service = build_default_analysis_service(report_repository=InMemoryAnalysisReportRepository())
    repository = InMemoryAnalysisTaskRepository()
    failed = AnalysisTaskRecord(
        task_id="task-failed",
        symbol="600519",
        message="请全面分析",
        status=AnalysisStatus.FAILED.value,
        created_at="2026-07-01T00:00:00+00:00",
        updated_at="2026-07-01T00:00:00+00:00",
        error="boom",
    )
    repository.save(failed)
    app = HttpApiApp(
        service=service,
        price_providers={"sina": FakePriceProvider()},
        task_queue=InMemoryAnalysisTaskQueue(service=service, repository=repository, executor=lambda operation: operation()),
    )

    response = app.handle("POST", "/tasks/task-failed/retry", b"")

    assert response.status == 202
    payload = decode(response)
    assert payload["task_id"] != "task-failed"
    assert payload["symbol"] == "600519"


def test_http_backtest_report() -> None:
    app = build_app()
    response = app.handle("POST", "/analysis", json.dumps({"symbol": "贵州茅台", "message": "请全面分析"}).encode("utf-8"))
    payload = decode(response)
    backtest_response = app.handle(
        "POST",
        f"/reports/{payload['task_id']}/backtest",
        json.dumps({"prices": [{"date": "2026-07-01", "close": 100.0}, {"date": "2026-07-03", "close": 116.0}]}).encode("utf-8"),
    )

    assert backtest_response.status == 200
    assert decode(backtest_response)["exit_reason"] == "take_profit"


def test_http_backtest_report_accepts_options() -> None:
    app = build_app()
    response = app.handle("POST", "/analysis", json.dumps({"symbol": "贵州茅台", "message": "请全面分析"}).encode("utf-8"))
    payload = decode(response)
    backtest_response = app.handle(
        "POST",
        f"/reports/{payload['task_id']}/backtest",
        json.dumps(
            {
                "prices": [{"date": "2026-07-01", "close": 100.0}, {"date": "2026-07-03", "close": 112.0}],
                "options": {"cost_pct": 0.001, "slippage_pct": 0.002, "adjustment": "qfq"},
            }
        ).encode("utf-8"),
    )

    assert backtest_response.status == 200
    payload = decode(backtest_response)
    assert payload["gross_return_pct"] == 0.12
    assert payload["return_pct"] == 0.1133
    assert payload["options"]["adjustment"] == "qfq"


def test_http_backtest_report_with_sina_source() -> None:
    app = build_app()
    response = app.handle("POST", "/analysis", json.dumps({"symbol": "贵州茅台", "message": "请全面分析"}).encode("utf-8"))
    payload = decode(response)

    backtest_response = app.handle(
        "POST",
        f"/reports/{payload['task_id']}/backtest",
        json.dumps({"source": "sina", "limit": 2}).encode("utf-8"),
    )

    assert backtest_response.status == 200
    assert decode(backtest_response)["exit_reason"] == "take_profit"


def test_http_portfolio_risk_budget() -> None:
    app = build_app()
    first = decode(app.handle("POST", "/analysis", json.dumps({"symbol": "贵州茅台", "message": "请全面分析"}).encode("utf-8")))
    second = decode(app.handle("POST", "/analysis", json.dumps({"symbol": "平安银行", "message": "请全面分析"}).encode("utf-8")))

    response = app.handle(
        "POST",
        "/portfolio/risk-budget",
        json.dumps({"task_ids": [first["task_id"], second["task_id"]]}).encode("utf-8"),
    )

    assert response.status == 200
    payload = decode(response)
    assert payload["total_position_pct"] > 0
    assert [position["stock"]["code"] for position in payload["positions"]] == ["600519", "000001"]


def test_http_responses_include_cors_headers() -> None:
    response = build_app().handle("GET", "/health", b"")

    assert response.headers["Access-Control-Allow-Origin"] == "*"


def test_http_options_preflight() -> None:
    response = build_app().handle("OPTIONS", "/analysis", b"")

    assert response.status == 204
    assert "POST" in response.headers["Access-Control-Allow-Methods"]


def test_run_http_server_is_exported() -> None:
    assert callable(run_http_server)
