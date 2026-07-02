import json

from money_api.api.http import HttpApiApp
from money_api.api.v1.router import build_default_analysis_service, build_default_research_tool_service, build_runtime_research_tool_service
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


def _fake_tencent_transport(url: str) -> str:
    values = [""] * 53
    values[1] = "贵州茅台"
    values[3] = "1688.00"
    values[32] = "2.50"
    values[39] = "28.50"
    values[46] = "9.10"
    return 'v_sh600519="' + "~".join(values) + '";'


def _fake_kline_transport(url: str) -> str:
    return json.dumps(
        [
            {"day": "2026-06-01", "close": 1600.0},
            {"day": "2026-06-02", "close": 1610.0},
            {"day": "2026-06-03", "close": 1620.0},
            {"day": "2026-06-04", "close": 1630.0},
            {"day": "2026-06-05", "close": 1640.0},
            {"day": "2026-06-06", "close": 1650.0},
        ],
        ensure_ascii=False,
    )


def _fake_eastmoney_transport(url: str) -> str:
    if "RPT_PCF10_FINANCEMAINFINADATA" in url:
        payload = {
            "result": {
                "data": [
                    {
                        "REPORT_DATE": "2026-03-31",
                        "REPORT_TYPE": "Q1",
                        "EPSJB": 8.88,
                        "BPS": 42.0,
                        "TOTAL_OPERATEINCOME": 1000.0,
                        "TOTAL_OPERATEINCOME_LAST": 880.0,
                        "PARENT_NETPROFIT": 380.0,
                        "PARENT_NETPROFIT_LAST": 320.0,
                        "TOTALOPERATEREVETZ": 13.64,
                        "PARENTNETPROFITTZ": 18.75,
                        "ROEJQ": 18.0,
                        "XSMLL": 35.0,
                        "ZCFZL": 28.0,
                        "TOTAL_SHARE": 1250.0,
                        "FREE_SHARE": 980.0,
                    }
                ]
            }
        }
    elif "RPT_F10_QTR_MAINFINADATA" in url:
        payload = {"result": {"data": [{"REPORT_DATE": "2026-03-31", "EPSJB": 2.1, "BPS": 41.0, "TOTALOPERATEREVE": 300.0, "PARENTNETPROFIT": 110.0, "TOTALOPERATEREVETZ": 11.0, "PARENTNETPROFITTZ": 12.0, "ROE_DILUTED": 4.5, "GROSS_PROFIT_RATIO": 33.0}]}}
    elif "RPT_HSF10_RESPREDICT_STATISTICS" in url:
        payload = {"result": {"data": [{"YEAR": "2026", "EPS": 8.8, "EPS_RATIO": 15.0, "PE": 27.5}]}}
    elif "RPT_STOCKVALUATIONTANTILE" in url:
        payload = {"result": {"data": [{"STATISTICS_CYCLE": 3, "INDEX_TYPE": 1, "PERCENTILE_THIRTY": 22.0, "PERCENTILE_FIFTY": 30.0, "PERCENTILE_SEVENTY": 45.0}]}}
    elif "RPT_MARGIN_STATISTICS_STOCKS" in url:
        payload = {"result": {"data": [{"TRADE_DATE": "2026-07-01", "FIN_BUY_AMT": 100.0, "FIN_REPAY_AMT": 60.0, "FIN_BALANCE": 480.0, "LOAN_SELL_VOL": 1.0, "LOAN_REPAY_VOL": 0.5, "LOAN_BALANCE": 20.0}]}}
    elif "RPT_STOCK_MAINFUND_FLOW" in url:
        payload = {"result": {"data": [{"TRADE_DATE": "2026-07-01", "MAIN_NET_INFLOW": 120.0, "MAIN_NET_INFLOW_RATE": 1.8, "MAIN_BUY": 240.0, "MAIN_SELL": 120.0}]}}
    elif "RPT_DAILYBILLBOARD_DETAILS" in url:
        payload = {"result": {"data": [{"TRADE_DATE": "2026-07-01", "BUY_AMT": 100.0, "SELL_AMT": 62.0, "NET_AMT": 38.0, "ORGAN_AMT": 15.0}]}}
    elif "RPT_STOCK_LIFTING_SCHEDULE" in url:
        payload = {"result": {"data": [{"UNLOCK_DATE": "2026-07-15", "UNLOCK_NUM": 1000.0, "UNLOCK_VALUE": 32000.0, "UNLOCK_RATIO": 3.2}]}}
    else:
        payload = {"result": {"data": []}}
    return json.dumps(payload, ensure_ascii=False)


def build_app(research_tools=None) -> HttpApiApp:
    service = build_default_analysis_service(report_repository=InMemoryAnalysisReportRepository())
    return HttpApiApp(
        service=service,
        price_providers={"sina": FakePriceProvider()},
        task_queue=InMemoryAnalysisTaskQueue(
            service=service,
            repository=InMemoryAnalysisTaskRepository(),
            executor=lambda operation: operation(),
        ),
        research_tools=research_tools or build_default_research_tool_service(),
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
    assert payload["engine_source"] == "mock"
    assert payload["data_sources"] == ["static"]
    assert payload["data_context"]["events"][0]["event_type"] == "earnings_forecast"
    assert payload["data_context"]["events"][0]["evidence_excerpt"] == "示例公司发布2026年半年度业绩预告"
    assert payload["investment_plan"]["direction"] == "buy"
    assert payload["data_trust"]["score"] <= 100
    assert payload["engine_telemetry"]["estimated_request_count"] >= 1
    assert payload["engine_cost_guardrail"]["summary"]
    assert report["task_id"] == payload["task_id"]


def test_http_list_reports() -> None:
    app = build_app()
    app.handle("POST", "/analysis", json.dumps({"symbol": "贵州茅台", "message": "请全面分析"}).encode("utf-8"))

    response = app.handle("GET", "/reports?limit=5", b"")

    assert response.status == 200
    assert decode(response)[0]["stock"]["code"] == "600519"
    assert decode(response)[0]["data_sources"] == ["static"]


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


def test_http_create_analysis_task_accepts_max_retries() -> None:
    app = build_app()

    response = app.handle(
        "POST",
        "/tasks/analysis",
        json.dumps({"symbol": "贵州茅台", "message": "请全面分析", "max_retries": 2}).encode("utf-8"),
    )

    assert response.status == 202
    assert decode(response)["max_retries"] == 2


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


def test_http_task_exposes_retry_observability_fields() -> None:
    service = build_default_analysis_service(report_repository=InMemoryAnalysisReportRepository())
    repository = InMemoryAnalysisTaskRepository()
    queue = InMemoryAnalysisTaskQueue(service=service, repository=repository, executor=lambda operation: None)
    failed = AnalysisTaskRecord(
        task_id="task-failed-timeout",
        symbol="600519",
        message="请全面分析",
        status=AnalysisStatus.FAILED.value,
        created_at="2026-07-01T00:00:00+00:00",
        updated_at="2026-07-01T00:00:00+00:00",
        retry_count=0,
        max_retries=1,
        error="task timed out after 1s",
    )
    repository.save(failed)
    queue._records[failed.task_id] = failed
    queue._now = lambda: "2026-07-01T00:00:05+00:00"  # type: ignore[attr-defined]
    app = HttpApiApp(service=service, price_providers={"sina": FakePriceProvider()}, task_queue=queue)

    response = app.handle("GET", "/tasks/task-failed-timeout", b"")

    assert response.status == 200
    payload = decode(response)
    assert payload["next_retry_delay_s"] == 2
    assert payload["next_retry_policy"] == "timeout"


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


def test_http_research_context_exposes_online_sources() -> None:
    app = build_app(
        research_tools=build_runtime_research_tool_service(
            quote_transport=_fake_tencent_transport,
            kline_transport=_fake_kline_transport,
            eastmoney_transport=_fake_eastmoney_transport,
            iwencai_api_key="test-key",
            iwencai_transport=lambda url: json.dumps(
                {
                    "status_code": 0,
                    "status_msg": "ok",
                    "code_count": 1,
                    "datas": [{"股票代码": "600519", "机构评分": 88}],
                    "chunks_info": [],
                },
                ensure_ascii=False,
            ),
        )
    )

    response = app.handle("POST", "/research/context", json.dumps({"symbol": "贵州茅台"}).encode("utf-8"))

    payload = decode(response)
    assert response.status == 200
    assert payload["stock"]["code"] == "600519"
    assert payload["data_sources"][0] == "tencent"
    assert payload["data_context"]["fundamentals"]["latest_finance"]["report_date"] == "2026-03-31"


def test_http_research_fundamentals_exposes_provider_chain() -> None:
    app = build_app(
        research_tools=build_runtime_research_tool_service(
            quote_transport=_fake_tencent_transport,
            kline_transport=_fake_kline_transport,
            eastmoney_transport=_fake_eastmoney_transport,
            iwencai_api_key="test-key",
            iwencai_transport=lambda url: json.dumps(
                {
                    "status_code": 0,
                    "status_msg": "ok",
                    "code_count": 1,
                    "datas": [{"股票代码": "600519", "机构评分": 88}],
                    "chunks_info": [],
                },
                ensure_ascii=False,
            ),
        )
    )

    response = app.handle("POST", "/research/fundamentals", json.dumps({"symbol": "贵州茅台"}).encode("utf-8"))

    payload = decode(response)
    assert response.status == 200
    assert payload["result"]["source"] == "eastmoney+iwencai"
    assert payload["result"]["data"]["rows"][0]["股票代码"] == "600519"


def test_http_research_extra_endpoints_expose_sources() -> None:
    app = build_app(
        research_tools=build_runtime_research_tool_service(
            quote_transport=_fake_tencent_transport,
            kline_transport=_fake_kline_transport,
            eastmoney_transport=_fake_eastmoney_transport,
        )
    )

    capital_flow = decode(app.handle("POST", "/research/capital-flow", json.dumps({"symbol": "贵州茅台"}).encode("utf-8")))
    longhubang = decode(app.handle("POST", "/research/longhubang", json.dumps({"symbol": "贵州茅台"}).encode("utf-8")))
    unlocks = decode(app.handle("POST", "/research/unlocks", json.dumps({"symbol": "贵州茅台"}).encode("utf-8")))

    assert capital_flow["result"]["ok"] is True
    assert capital_flow["result"]["data"]["rows"][0]["MAIN_NET_INFLOW"] == 120.0
    assert longhubang["result"]["ok"] is True
    assert longhubang["result"]["data"]["rows"][0]["NET_AMT"] == 38.0
    assert unlocks["result"]["ok"] is True
    assert unlocks["result"]["data"]["rows"][0]["UNLOCK_DATE"] == "2026-07-15"


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
