from money_api.api.v1.router import (
    build_default_analysis_service,
    build_runtime_analysis_service,
    build_tencent_quote_analysis_service,
    build_tradingagents_analysis_service,
)
from money_api.domains.analysis.contracts import BacktestPricePoint
from money_api.domains.analysis.tradingagents_engine import FakeTradingAgentsRunner
from money_api.main import analyze_stock, backtest_analysis_report, build_portfolio_risk_budget, get_analysis_report, health, list_analysis_reports


def _fake_tencent_transport(url: str) -> str:
    values = [""] * 53
    values[1] = "贵州茅台"
    values[3] = "1688.00"
    values[32] = "2.50"
    values[39] = "28.50"
    values[46] = "9.10"
    return 'v_sh600519="' + "~".join(values) + '";'


def _fake_kline_transport(url: str) -> str:
    return str(
        [
            {"day": "2026-06-01", "close": 1600.0},
            {"day": "2026-06-02", "close": 1610.0},
            {"day": "2026-06-03", "close": 1620.0},
            {"day": "2026-06-04", "close": 1630.0},
            {"day": "2026-06-05", "close": 1640.0},
            {"day": "2026-06-06", "close": 1650.0},
        ]
    ).replace("'", '"')


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
        payload = {
            "result": {
                "data": [
                    {
                        "REPORT_DATE": "2026-03-31",
                        "EPSJB": 2.1,
                        "BPS": 41.0,
                        "TOTALOPERATEREVE": 300.0,
                        "PARENTNETPROFIT": 110.0,
                        "TOTALOPERATEREVETZ": 11.0,
                        "PARENTNETPROFITTZ": 12.0,
                        "ROE_DILUTED": 4.5,
                        "GROSS_PROFIT_RATIO": 33.0,
                    }
                ]
            }
        }
    elif "RPT_HSF10_RESPREDICT_STATISTICS" in url:
        payload = {"result": {"data": [{"YEAR": "2026", "EPS": 8.8, "EPS_RATIO": 15.0, "PE": 27.5}]}}
    elif "RPT_STOCKVALUATIONTANTILE" in url:
        payload = {"result": {"data": [{"STATISTICS_CYCLE": 3, "INDEX_TYPE": 1, "PERCENTILE_THIRTY": 22.0, "PERCENTILE_FIFTY": 30.0, "PERCENTILE_SEVENTY": 45.0}]}}
    elif "RPT_MARGIN_STATISTICS_STOCKS" in url:
        payload = {"result": {"data": [{"TRADE_DATE": "2026-07-01", "FIN_BUY_AMT": 100.0, "FIN_REPAY_AMT": 60.0, "FIN_BALANCE": 480.0, "LOAN_SELL_VOL": 1.0, "LOAN_REPAY_VOL": 0.5, "LOAN_BALANCE": 20.0}]}}
    else:
        payload = {"result": {"data": []}}
    import json

    return json.dumps(payload, ensure_ascii=False)


def test_analyze_stock_api_returns_serialized_report() -> None:
    payload = analyze_stock("贵州茅台", "请全面分析并给出投资建议")

    assert payload["stock"]["code"] == "600519"
    assert payload["status"] == "report_ready"
    assert payload["summary"]
    assert payload["agent_views"]
    assert payload["risk_controls"]["max_position_pct"] <= 0.1
    assert payload["investment_plan"]["direction"] in {"buy", "watch", "sell", "wait"}
    assert payload["data_trust"]["score"] <= 100
    assert payload["engine_telemetry"]["execution_path"] in {"primary", "quick", "fallback"}
    assert payload["engine_cost_guardrail"]["status"] in {"ok", "warn", "over_budget"}

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
    assert payload["engine_source"] == "mock"
    assert payload["data_sources"] == ["static"]
    assert payload["data_context"]["events"][0]["event_type"] == "earnings_forecast"
    assert payload["data_context"]["events"][0]["priority"] == "high"
    assert payload["data_context"]["events"][0]["evidence_excerpt"] == "示例公司发布2026年半年度业绩预告"
    assert payload["investment_plan"]["direction"] == "buy"
    assert payload["data_trust"]["level"] in {"high", "medium", "low"}
    assert payload["engine_telemetry"]["cost_tier"] in {"low", "high"}
    assert payload["engine_cost_guardrail"]["max_cost_tier"] in {"medium", "high"}


def test_tencent_quote_service_factory_accepts_transport() -> None:
    service = build_tencent_quote_analysis_service(
        transport=_fake_tencent_transport,
        news_transport=lambda url: (
            'callback({"result":{"cmsArticleWebOld":[{"title":"茅台业绩稳健","content":"季度表现稳定",'
            '"date":"2026-07-01 09:30:00","mediaName":"东方财富","url":"https://example.com/news/1"}]}})'
        ),
        flash_transport=lambda url: {"data": {"roll_data": [{"title": "央行公开市场操作", "brief": "今日开展逆回购操作", "ctime": "1782879000"}]}},
        bulletin_transport=lambda url: """
        <html><body><div class='datelist'><ul>
          <li>2026-05-09 <a href='https://vip.stock.finance.sina.com.cn/bulletin/1'>协鑫能科：关于对控股子公司提供担保的进展公告</a></li>
        </ul></div></body></html>
        """,
        kline_transport=_fake_kline_transport,
        eastmoney_transport=_fake_eastmoney_transport,
    )
    payload = service.create_single_stock_analysis("贵州茅台", "请全面分析").to_dict()

    assert payload["data_diagnostics"][0]["source"] == "tencent"
    assert payload["data_diagnostics"][1]["source"] == "sina"
    assert payload["data_diagnostics"][2]["source"].startswith("eastmoney")
    assert "tencent" in payload["data_sources"]
    assert any(source.startswith("eastmoney") for source in payload["data_sources"])


def test_tencent_quote_service_factory_uses_bulletin_detail_content() -> None:
    service = build_tencent_quote_analysis_service(
        transport=_fake_tencent_transport,
        news_transport=lambda url: 'callback({"result":{"cmsArticleWebOld":[]}})',
        flash_transport=lambda url: {"data": {"roll_data": []}},
        bulletin_transport=lambda url: (
            """
            <html><body><div class='datelist'><ul>
              <li>2026-05-09 <a href='https://vip.stock.finance.sina.com.cn/bulletin/1'>公司公告</a></li>
            </ul></div></body></html>
            """
            if "AllBulletin" in url
            else """
            <html><body>
              <div id='artibody'>
                <p>公告正文说明控股股东拟减持不超过1%股份。</p>
              </div>
            </body></html>
            """
        ),
        kline_transport=_fake_kline_transport,
        eastmoney_transport=_fake_eastmoney_transport,
    )

    payload = service.create_single_stock_analysis("贵州茅台", "请全面分析").to_dict()

    assert payload["data_context"]["events"][0]["event_type"] == "share_reduction"
    assert payload["data_context"]["events"][0]["evidence_scope"] == "content"
    assert "减持" in payload["data_context"]["events"][0]["evidence_excerpt"]


def test_tradingagents_service_factory_accepts_runner() -> None:
    service = build_tradingagents_analysis_service(runner=FakeTradingAgentsRunner())
    payload = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议").to_dict()

    assert payload["status"] == "report_ready"
    assert payload["data_diagnostics"][-1]["source"] == "fake-tradingagents"
    assert payload["engine_source"] == "fake-tradingagents"


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

    service = build_runtime_analysis_service(
        transport=_fake_tencent_transport,
        news_transport=lambda url: (
            'callback({"result":{"cmsArticleWebOld":[{"title":"茅台业绩稳健","content":"季度表现稳定",'
            '"date":"2026-07-01 09:30:00","mediaName":"东方财富","url":"https://example.com/news/1"}]}})'
        ),
        flash_transport=lambda url: {"data": {"roll_data": [{"title": "央行公开市场操作", "brief": "今日开展逆回购操作", "ctime": "1782879000"}]}},
        bulletin_transport=lambda url: """
        <html><body><div class='datelist'><ul>
          <li>2026-05-09 <a href='https://vip.stock.finance.sina.com.cn/bulletin/1'>协鑫能科：关于对控股子公司提供担保的进展公告</a></li>
        </ul></div></body></html>
        """,
        kline_transport=_fake_kline_transport,
        eastmoney_transport=_fake_eastmoney_transport,
        tradingagents_runner=FakeTradingAgentsRunner(),
    )
    payload = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议").to_dict()

    assert payload["data_diagnostics"][0]["source"] == "tencent"
    assert payload["data_diagnostics"][1]["source"] == "sina"
    assert payload["data_diagnostics"][2]["source"].startswith("eastmoney")
    assert payload["data_diagnostics"][3]["source"] == "eastmoney+cls+sina-bulletin"
    assert payload["data_diagnostics"][-1]["source"] == "fake-tradingagents"
    assert payload["data_sources"][0] == "tencent"
    assert any(source.startswith("eastmoney") for source in payload["data_sources"])
    assert payload["engine_source"] == "fake-tradingagents"
    assert payload["engine_mode"] == "tradingagents"
    assert payload["summary"] == "贵州茅台 fake TradingAgents 分析完成。"
    assert payload["data_context"]["news"][0]["title"] == "茅台业绩稳健"
    assert payload["data_context"]["news"][1]["source"] == "CLS Wire"
    assert payload["data_context"]["news"][2]["source"] == "新浪公告"
    assert payload["data_context"]["events"][0]["event_type"] == "guarantee"
    assert payload["data_context"]["events"][0]["priority"] == "high"
    assert "担保" in payload["data_context"]["events"][0]["evidence_excerpt"]
    assert any("高优先级事件证据覆盖" in text or "高优先级事件主要来自正文命中" in text or "高优先级事件主要来自标题命中" in text for text in payload["investment_plan"]["rationale"])
    assert any("正文命中已进入计划解释" in text or "当前高优先级信号主要来自标题" in text or "标题与正文同时命中的事件较多" in text for text in payload["investment_plan"]["risk_notes"])
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
    assert payload["engine_source"] == "fake-tradingagents"
    assert "tencent" in payload["data_sources"]
    assert "static" not in payload["data_sources"]
    assert any(source.startswith("eastmoney") for source in payload["data_sources"])
    assert "fake-tradingagents" in payload["data_sources"]


def test_runtime_analysis_service_auto_mode_falls_back_to_tool_driven(monkeypatch) -> None:
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

    service = build_runtime_analysis_service(
        transport=_fake_tencent_transport,
        kline_transport=_fake_kline_transport,
        eastmoney_transport=_fake_eastmoney_transport,
        tradingagents_runner=FailingRunner(),
    )
    payload = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议").to_dict()

    assert payload["status"] == "report_ready"
    assert payload["agent_views"][0]["agent"] == "Market Tool Lens"
    assert payload["data_diagnostics"][-2]["source"] == "tradingagents"
    assert payload["data_diagnostics"][-1]["source"] == "tool-driven"
    assert payload["engine_source"] == "tool-driven"
    assert payload["engine_mode"] == "auto"
    assert "boom" in (payload["fallback_reason"] or "")
