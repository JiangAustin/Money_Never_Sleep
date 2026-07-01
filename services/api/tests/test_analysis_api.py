from money_api.api.v1.router import (
    build_default_analysis_service,
    build_runtime_analysis_service,
    build_tencent_quote_analysis_service,
    build_tradingagents_analysis_service,
)
from money_api.domains.analysis.contracts import BacktestPricePoint
from money_api.domains.analysis.tradingagents_engine import FakeTradingAgentsRunner
from money_api.main import analyze_stock, backtest_analysis_report, build_portfolio_risk_budget, get_analysis_report, health, list_analysis_reports


def test_analyze_stock_api_returns_serialized_report() -> None:
    payload = analyze_stock("贵州茅台", "请全面分析并给出投资建议")

    assert payload["stock"]["code"] == "600519"
    assert payload["status"] == "report_ready"
    assert payload["summary"]
    assert payload["agent_views"]
    assert payload["risk_controls"]["max_position_pct"] <= 0.1

    loaded = get_analysis_report(payload["task_id"])
    assert loaded == payload


def test_get_analysis_report_returns_none_for_missing_task() -> None:
    assert get_analysis_report("missing-task") is None


def test_health_api_still_returns_original_payload() -> None:
    assert health() == {"status": "ok", "service": "money-never-sleep-api"}


def test_default_analysis_service_stays_offline() -> None:
    payload = build_default_analysis_service().create_single_stock_analysis("贵州茅台", "请全面分析").to_dict()

    assert payload["stock"]["code"] == "600519"
    assert payload["data_diagnostics"][0]["source"] == "static"


def test_tencent_quote_service_factory_accepts_transport() -> None:
    def transport(url: str) -> str:
        values = [""] * 53
        values[1] = "贵州茅台"
        values[3] = "1688.00"
        return 'v_sh600519="' + "~".join(values) + '";'

    service = build_tencent_quote_analysis_service(transport=transport)
    payload = service.create_single_stock_analysis("贵州茅台", "请全面分析").to_dict()

    assert payload["data_diagnostics"][0]["source"] == "tencent"


def test_tradingagents_service_factory_accepts_runner() -> None:
    service = build_tradingagents_analysis_service(runner=FakeTradingAgentsRunner())
    payload = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议").to_dict()

    assert payload["status"] == "report_ready"
    assert payload["data_diagnostics"][-1]["source"] == "fake-tradingagents"


def test_list_analysis_reports_returns_recent_records() -> None:
    payload = analyze_stock("贵州茅台", "请全面分析并给出投资建议")

    records = list_analysis_reports(limit=5)

    assert records
    assert records[0]["task_id"] == payload["task_id"]
    assert records[0]["stock"]["code"] == "600519"


def test_backtest_analysis_report_returns_result() -> None:
    payload = analyze_stock("贵州茅台", "请全面分析并给出投资建议")
    result = backtest_analysis_report(
        payload["task_id"],
        [
            {"date": "2026-07-01", "close": 100.0},
            {"date": "2026-07-02", "close": 108.0},
            {"date": "2026-07-03", "close": 116.0},
        ],
    )

    assert result["task_id"] == payload["task_id"]
    assert result["exit_reason"] == "take_profit"


def test_backtest_analysis_report_accepts_options() -> None:
    payload = analyze_stock("贵州茅台", "请全面分析并给出投资建议")
    result = backtest_analysis_report(
        payload["task_id"],
        [
            {"date": "2026-07-01", "close": 100.0},
            {"date": "2026-07-02", "close": 112.0},
        ],
        options={"cost_pct": 0.001, "slippage_pct": 0.002, "adjustment": "qfq"},
    )

    assert result["gross_return_pct"] == 0.12
    assert result["return_pct"] == 0.1133
    assert result["options"]["adjustment"] == "qfq"


def test_backtest_analysis_report_accepts_price_provider() -> None:
    class FakePriceProvider:
        def get_price_series(self, stock, limit=60):
            from money_api.domains.market_data.provider_results import ProviderResult

            return ProviderResult(
                kind="price_series",
                source="fake",
                ok=True,
                data=[BacktestPricePoint(date="2026-07-01", close=100.0), BacktestPricePoint(date="2026-07-02", close=116.0)],
            )

    service = build_default_analysis_service()
    payload = service.create_single_stock_analysis("贵州茅台", "请全面分析").to_dict()
    result = service.backtest_report_from_provider(payload["task_id"], FakePriceProvider(), limit=2)

    assert result.exit_reason == "take_profit"


def test_build_portfolio_risk_budget_returns_serialized_budget() -> None:
    first = analyze_stock("贵州茅台", "请全面分析并给出投资建议")
    second = analyze_stock("平安银行", "请全面分析并给出投资建议")

    budget = build_portfolio_risk_budget([first["task_id"], second["task_id"]])

    assert budget["total_position_pct"] > 0
    assert budget["cash_reserve_pct"] < 1
    assert [position["stock"]["code"] for position in budget["positions"]] == ["600519", "000001"]


def test_runtime_analysis_service_uses_tencent_quote_by_default(monkeypatch) -> None:
    monkeypatch.delenv("MONEY_MARKET_DATA_MODE", raising=False)
    monkeypatch.delenv("MONEY_DEEP_ENGINE", raising=False)

    def transport(url: str) -> str:
        values = [""] * 53
        values[1] = "贵州茅台"
        values[3] = "1688.00"
        return 'v_sh600519="' + "~".join(values) + '";'

    def news_transport(url: str) -> str:
        return (
            'callback({"result":{"cmsArticleWebOld":[{"title":"茅台业绩稳健","content":"季度表现稳定",'
            '"date":"2026-07-01 09:30:00","mediaName":"东方财富","url":"https://example.com/news/1"}]}})'
        )

    def flash_transport(url: str):
        return {"data": {"roll_data": [{"title": "央行公开市场操作", "brief": "今日开展逆回购操作", "ctime": "1782879000"}]}}

    def bulletin_transport(url: str) -> str:
        return """
        <html><body><div class='datelist'><ul>
          <li>2026-05-09 <a href='https://vip.stock.finance.sina.com.cn/bulletin/1'>协鑫能科：关于对控股子公司提供担保的进展公告</a></li>
        </ul></div></body></html>
        """

    service = build_runtime_analysis_service(
        transport=transport,
        news_transport=news_transport,
        flash_transport=flash_transport,
        bulletin_transport=bulletin_transport,
        tradingagents_runner=FakeTradingAgentsRunner(),
    )
    payload = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议").to_dict()

    assert payload["data_diagnostics"][0]["source"] == "tencent"
    assert payload["data_diagnostics"][3]["source"] == "eastmoney+cls+sina-bulletin"
    assert payload["data_diagnostics"][-1]["source"] == "fake-tradingagents"
    assert payload["summary"] == "贵州茅台 fake TradingAgents 分析完成。"
    assert payload["data_context"]["news"][0]["title"] == "茅台业绩稳健"
    assert payload["data_context"]["news"][1]["source"] == "CLS Wire"
    assert payload["data_context"]["news"][2]["source"] == "新浪公告"
    assert payload["agent_views"][0]["agent"] == "TradingAgents market"


def test_runtime_analysis_service_accepts_tradingagents_runner(monkeypatch) -> None:
    monkeypatch.setenv("MONEY_DEEP_ENGINE", "tradingagents")

    def transport(url: str) -> str:
        values = [""] * 53
        values[1] = "贵州茅台"
        values[3] = "1688.00"
        return 'v_sh600519="' + "~".join(values) + '";'

    service = build_runtime_analysis_service(transport=transport, tradingagents_runner=FakeTradingAgentsRunner())
    payload = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议").to_dict()

    assert payload["data_diagnostics"][-1]["source"] == "fake-tradingagents"


def test_runtime_analysis_service_auto_mode_falls_back_to_mock(monkeypatch) -> None:
    monkeypatch.delenv("MONEY_DEEP_ENGINE", raising=False)

    class FailingRunner:
        def run(self, request):
            from money_api.domains.analysis.tradingagents_engine import TradingAgentsRunResult

            return TradingAgentsRunResult(
                ok=False,
                source="tradingagents",
                diagnostics=[{"kind": "deep_engine", "source": "tradingagents", "ok": False}],
                error_type="RuntimeError",
                error_message="boom",
            )

    def transport(url: str) -> str:
        values = [""] * 53
        values[1] = "贵州茅台"
        values[3] = "1688.00"
        return 'v_sh600519="' + "~".join(values) + '";'

    service = build_runtime_analysis_service(transport=transport, tradingagents_runner=FailingRunner())
    payload = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议").to_dict()

    assert payload["status"] == "report_ready"
    assert payload["agent_views"][0]["agent"] == "Mock Research Engine"
    assert payload["data_diagnostics"][-2]["source"] == "tradingagents"
    assert payload["data_diagnostics"][-1]["source"] == "mock-fallback"