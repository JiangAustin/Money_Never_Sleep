from money_api.domains.analysis.contracts import DataContext, StockIdentity
from money_api.domains.analysis.tradingagents_engine import (
    FakeTradingAgentsRunner,
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
