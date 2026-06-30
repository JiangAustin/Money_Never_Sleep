from money_api.domains.analysis.agent_engine import MockDeepResearchEngine, QuickAgentRouter
from money_api.domains.analysis.context_builder import DataContextBuilder, StaticMarketDataProvider
from money_api.domains.analysis.service import AnalysisService
from money_api.domains.market_data.resolver import StockResolver


def build_service() -> AnalysisService:
    return AnalysisService(
        resolver=StockResolver(name_map={"贵州茅台": "600519"}),
        context_builder=DataContextBuilder(
            StaticMarketDataProvider(
                quote={"price": 1688.0},
                technicals={"ma5": 1660.0},
                fundamentals={"pe_ttm": 28.5},
                news=[{"title": "业绩稳定"}],
            )
        ),
        quick_router=QuickAgentRouter(),
        deep_engine=MockDeepResearchEngine(),
    )


def test_create_single_stock_analysis_returns_report() -> None:
    service = build_service()

    report = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议")

    assert report.stock.code == "600519"
    assert report.status.value == "report_ready"
    assert report.summary
    assert service.get_report(report.task_id) == report


def test_lightweight_question_uses_quick_summary() -> None:
    service = build_service()

    report = service.create_single_stock_analysis("600519", "现在多少钱")

    assert report.action.value == "watch"
    assert report.agent_views[0].agent == "Quick Agent"