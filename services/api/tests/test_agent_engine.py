from money_api.domains.analysis.agent_engine import MockDeepResearchEngine, QuickAgentRouter
from money_api.domains.analysis.contracts import DataContext, StockIdentity


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