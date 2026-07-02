from money_api.domains.analysis.tradingagents_engine import TradingAgentsDeepResearchEngine, TradingAgentsRunRequest
from money_api.integrations.tradingagents_runner import TradingAgentsGraphRunner


class FakeGraph:
    instances = []

    def __init__(self, selected_analysts, debug, config):
        self.selected_analysts = selected_analysts
        self.debug = debug
        self.config = config
        FakeGraph.instances.append(self)

    def propagate(self, company_name, trade_date):
        return (
            {
                "market_report": "市场报告",
                "sentiment_report": "舆情报告",
                "news_report": "新闻报告",
                "fundamentals_report": "基本面报告",
                "policy_report": "政策报告",
                "hot_money_report": "游资报告",
                "lockup_report": "解禁报告",
                "investment_debate_state": {
                    "bull_history": "多方观点",
                    "bear_history": "空方观点",
                    "judge_decision": "研究经理结论",
                },
                "risk_debate_state": {
                    "aggressive_history": "激进风险观点",
                    "conservative_history": "保守风险观点",
                    "neutral_history": "中性风险观点",
                    "judge_decision": "组合经理结论",
                },
                "investment_plan": "投资计划摘要",
                "trader_investment_plan": "交易员执行计划",
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
    assert result.agent_reports["social"] == "舆情报告"
    assert result.agent_reports["bull_researcher"] == "多方观点"
    assert result.agent_reports["portfolio_manager"] == "组合经理结论"


def test_graph_runner_uses_astock_defaults_and_runtime_paths() -> None:
    FakeGraph.instances = []
    request = TradingAgentsRunRequest(
        task_id="task-1",
        code="600519",
        name="贵州茅台",
        market="cn",
        trade_date="2026-07-01",
        context_snapshot={},
        diagnostics=[],
    )

    result = TradingAgentsGraphRunner(
        graph_factory=FakeGraph,
        config={"llm_provider": "deepseek", "deep_think_llm": "deepseek-chat"},
    ).run(request)

    assert result.ok is True
    assert FakeGraph.instances[0].selected_analysts == [
        "market",
        "social",
        "news",
        "fundamentals",
        "policy",
        "hot_money",
        "lockup",
    ]
    assert FakeGraph.instances[0].config["output_language"] == "Chinese"
    assert FakeGraph.instances[0].config["max_debate_rounds"] == 1
    assert FakeGraph.instances[0].config["max_risk_discuss_rounds"] == 1
    assert FakeGraph.instances[0].config["llm_provider"] == "deepseek"
    assert FakeGraph.instances[0].config["deep_think_llm"] == "deepseek-chat"
    assert result.diagnostics[-1]["selected_analysts"] == FakeGraph.instances[0].selected_analysts
    assert result.diagnostics[-1]["provider"] == "deepseek"
    assert result.diagnostics[-1]["deep_model"] == "deepseek-chat"
    assert result.diagnostics[-1]["runtime_ms"] >= 0


def test_graph_runner_diagnostics_include_context_snapshot_and_failure_details() -> None:
    class RaisingGraph(FakeGraph):
        def propagate(self, company_name, trade_date):
            raise RuntimeError("boom")

    request = TradingAgentsRunRequest(
        task_id="task-1",
        code="600519",
        name="贵州茅台",
        market="cn",
        trade_date="2026-07-01",
        context_snapshot={"events": [{"event_type": "share_reduction"}], "gaps": ["fund_flow"]},
        diagnostics=[],
    )

    result = TradingAgentsGraphRunner(graph_factory=RaisingGraph).run(request)

    assert result.ok is False
    assert result.diagnostics[-1]["ok"] is False
    assert result.diagnostics[-1]["error_type"] == "RuntimeError"
    assert result.diagnostics[-1]["error_message"] == "boom"
    assert result.diagnostics[-1]["context_snapshot"]["events"][0]["event_type"] == "share_reduction"


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


def test_tradingagents_engine_marks_unknown_decision_fallback() -> None:
    class UnknownDecisionRunner:
        def run(self, request):
            from money_api.domains.analysis.tradingagents_engine import TradingAgentsRunResult

            assert isinstance(request.context_snapshot, dict)
            return TradingAgentsRunResult(
                ok=True,
                source="tradingagents",
                final_decision="STRONG_BUY",
                summary="未知决策测试",
                agent_reports={"portfolio_manager": "组合经理给出无法识别的动作"},
            )

    from money_api.domains.analysis.contracts import DataContext, DecisionAction, StockIdentity

    context = DataContext(stock=StockIdentity(code="600519", name="贵州茅台"))
    report = TradingAgentsDeepResearchEngine(UnknownDecisionRunner()).analyze("task-1", context)

    assert report.action == DecisionAction.WATCH
    assert any("无法识别" in risk.message for risk in report.risks)
