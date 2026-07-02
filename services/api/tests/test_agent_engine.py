from money_api.domains.analysis.agent_engine import MockDeepResearchEngine, QuickAgentRouter
from money_api.domains.analysis.contracts import DataContext, StockIdentity
from money_api.domains.analysis.tool_driven_engine import ToolDrivenResearchEngine


def test_quick_router_detects_deep_analysis_request() -> None:
    router = QuickAgentRouter()

    assert router.needs_deep_analysis("请全面分析贵州茅台并给出投资建议") is True
    assert router.needs_deep_analysis("贵州茅台现在多少钱") is False


def test_quick_router_handles_empty_or_invalid_messages() -> None:
    router = QuickAgentRouter()

    assert router.needs_deep_analysis("") is False
    assert router.needs_deep_analysis(None) is False  # type: ignore[arg-type]


def test_mock_engine_generates_report_with_low_confidence_when_gaps_exist() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    context = DataContext(stock=stock, quote={"price": 1688.0}, gaps=["news"])

    report = MockDeepResearchEngine().analyze("task-1", context)

    assert report.task_id == "task-1"
    assert report.stock == stock
    assert report.confidence.value == "low"
    assert report.action.value == "watch"
    assert report.agent_views[0].agent == "Mock Research Engine"


def test_mock_engine_generates_medium_confidence_without_gaps() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    context = DataContext(stock=stock, quote={"price": 1688.0})

    report = MockDeepResearchEngine().analyze("task-1", context)

    assert report.confidence.value == "medium"
    assert report.risks[0].level == "low"
    assert report.risks[0].message == "当前为 mock 分析，需接入真实投研引擎验证"


def test_tool_driven_engine_uses_live_context_signals() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    context = DataContext(
        stock=stock,
        quote={"price": 1688.0, "change_pct": 2.5, "pe_ttm": 28.5, "pb": 9.1},
        technicals={"latest_close": 1688.0, "ma5": 1660.0, "ma20": 1588.0},
        fundamentals={
            "latest_finance": {"revenue_yoy": 12.0, "net_profit_yoy": 15.0, "roe": 18.0, "gross_margin": 35.0},
            "quarterly_finance": [{"report_date": "2026-03-31"}],
            "valuation_percentile": {"percentile_50": 22.0},
            "predict_summary": [{"year": "2026", "eps": 8.88}],
            "iwencai": {"rows": [{"foo": "bar"}]},
        },
        news=[{"title": "贵州茅台发布业绩预告", "content": "同比增长", "source": "eastmoney"}],
        events=[],
        gaps=[],
        diagnostics=[{"kind": "quote", "source": "tencent", "ok": True}],
    )

    report = ToolDrivenResearchEngine().analyze("task-2", context)

    assert report.engine_source == "tool-driven"
    assert report.engine_mode == "tool-driven"
    assert report.status.value == "report_ready"
    assert report.action.value == "buy"
    assert report.confidence.value == "high"
    assert any(view.agent == "Fundamentals Tool Lens" for view in report.agent_views)
    assert "在线工具" in report.summary or "偏正面" in report.summary
