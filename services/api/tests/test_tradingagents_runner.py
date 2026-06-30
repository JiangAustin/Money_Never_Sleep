from money_api.domains.analysis.tradingagents_engine import TradingAgentsRunRequest
from money_api.integrations.tradingagents_runner import TradingAgentsGraphRunner


class FakeGraph:
    def __init__(self, selected_analysts, debug, config):
        self.selected_analysts = selected_analysts
        self.debug = debug
        self.config = config

    def propagate(self, company_name, trade_date):
        return (
            {
                "market_report": "市场报告",
                "news_report": "新闻报告",
                "fundamentals_report": "基本面报告",
                "policy_report": "政策报告",
                "hot_money_report": "游资报告",
                "lockup_report": "解禁报告",
                "final_trade_decision": "WATCH",
            },
            "WATCH",
        )


def test_graph_runner_uses_injected_graph_factory() -> None:
    request = TradingAgentsRunRequest(
        task_id="task-1",
        code="600519",
        name="贵州茅台",
        market="cn",
        trade_date="2026-07-01",
        context_snapshot={},
        diagnostics=[],
    )
    runner = TradingAgentsGraphRunner(graph_factory=FakeGraph, config={"output_language": "Chinese"})

    result = runner.run(request)

    assert result.ok is True
    assert result.source == "tradingagents"
    assert result.final_decision == "WATCH"
    assert result.agent_reports["market"] == "市场报告"


def test_graph_runner_returns_failure_when_graph_raises() -> None:
    class RaisingGraph(FakeGraph):
        def propagate(self, company_name, trade_date):
            raise RuntimeError("boom")

    request = TradingAgentsRunRequest(
        task_id="task-1",
        code="600519",
        name="贵州茅台",
        market="cn",
        trade_date="2026-07-01",
        context_snapshot={},
        diagnostics=[],
    )
    result = TradingAgentsGraphRunner(graph_factory=RaisingGraph).run(request)

    assert result.ok is False
    assert result.error_type == "RuntimeError"
    assert result.error_message == "boom"
