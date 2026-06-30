from money_api.domains.analysis.contracts import DataContext, StockIdentity
from money_api.domains.analysis.tradingagents_engine import (
    FakeTradingAgentsRunner,
    TradingAgentsDeepResearchEngine,
    TradingAgentsRunRequest,
    TradingAgentsRunResult,
)


def test_run_request_from_context_captures_snapshot() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    context = DataContext(
        stock=stock,
        quote={"price": 1688.0},
        technicals={"ma5": 1660.0},
        fundamentals={"pe_ttm": 28.5},
        news=[{"title": "业绩稳定"}],
        gaps=["news"],
        diagnostics=[{"kind": "quote", "source": "tencent", "ok": True}],
    )

    request = TradingAgentsRunRequest.from_context("task-1", context, trade_date="2026-07-01")

    assert request.task_id == "task-1"
    assert request.code == "600519"
    assert request.context_snapshot["quote"]["price"] == 1688.0
    assert request.context_snapshot["gaps"] == ["news"]
    assert request.diagnostics == [{"kind": "quote", "source": "tencent", "ok": True}]


def test_fake_runner_returns_success_result() -> None:
    request = TradingAgentsRunRequest(
        task_id="task-1",
        code="600519",
        name="贵州茅台",
        market="cn",
        trade_date="2026-07-01",
        context_snapshot={},
        diagnostics=[],
    )

    result = FakeTradingAgentsRunner().run(request)

    assert isinstance(result, TradingAgentsRunResult)
    assert result.ok is True
    assert result.source == "fake-tradingagents"
    assert result.final_decision == "WATCH"
    assert result.agent_reports["market"]


def test_tradingagents_engine_maps_success_result_to_report() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    context = DataContext(stock=stock, quote={"price": 1688.0})

    report = TradingAgentsDeepResearchEngine(FakeTradingAgentsRunner()).analyze("task-1", context)

    assert report.task_id == "task-1"
    assert report.status.value == "report_ready"
    assert report.action.value == "watch"
    assert report.confidence.value == "medium"
    assert report.summary == "贵州茅台 fake TradingAgents 分析完成。"
    assert report.agent_views[0].agent == "TradingAgents market"
    assert report.data_context.diagnostics[-1]["source"] == "fake-tradingagents"


class FailingTradingAgentsRunner:
    def run(self, request: TradingAgentsRunRequest) -> TradingAgentsRunResult:
        return TradingAgentsRunResult(
            ok=False,
            source="tradingagents",
            diagnostics=[{"kind": "deep_engine", "source": "tradingagents", "ok": False}],
            error_type="RuntimeError",
            error_message="boom",
        )


def test_tradingagents_engine_maps_failure_to_failed_report() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    context = DataContext(stock=stock, quote={"price": 1688.0})

    report = TradingAgentsDeepResearchEngine(FailingTradingAgentsRunner()).analyze("task-1", context)

    assert report.status.value == "failed"
    assert report.action.value == "watch"
    assert report.confidence.value == "low"
    assert report.risks[0].message == "TradingAgents 执行失败: boom"
    assert report.data_context.diagnostics[-1]["ok"] is False
