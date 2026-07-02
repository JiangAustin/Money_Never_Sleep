from money_api.domains.analysis.agent_engine import MockDeepResearchEngine, QuickAgentRouter
from money_api.domains.analysis.context_builder import DataContextBuilder, StaticMarketDataProvider
from money_api.domains.analysis.report_repository import InMemoryAnalysisReportRepository
from money_api.domains.analysis.service import AnalysisService
from money_api.domains.market_data.resolver import StockResolver


def build_service(repository=None) -> AnalysisService:
    return AnalysisService(
        resolver=StockResolver(name_map={"贵州茅台": "600519"}),
        context_builder=DataContextBuilder(
            StaticMarketDataProvider(
                quote={"price": 1688.0},
                technicals={"ma5": 1660.0},
                fundamentals={"pe_ttm": 28.5},
                news=[{"title": "示例公司发布2026年半年度业绩预告", "content": "预计同比增长"}],
            )
        ),
        quick_router=QuickAgentRouter(),
        deep_engine=MockDeepResearchEngine(),
        report_repository=repository,
    )


def test_create_single_stock_analysis_returns_report() -> None:
    service = build_service()

    report = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议")

    assert report.stock.code == "600519"
    assert report.status.value == "report_ready"
    assert report.summary
    assert report.risk_controls is not None
    assert report.investment_plan is not None
    assert report.investment_plan.direction.value == "buy"
    assert report.investment_plan.target_position_pct == report.risk_controls.max_position_pct
    assert report.data_trust is not None
    assert report.engine_telemetry is not None
    assert report.engine_cost_guardrail is not None
    assert report.engine_source == "mock"
    assert report.data_context.events[0].event_type.value == "earnings_forecast"
    assert report.data_context.events[0].priority == "high"
    assert service.get_report(report.task_id) == report


def test_lightweight_question_uses_quick_summary() -> None:
    service = build_service()

    report = service.create_single_stock_analysis("600519", "现在多少钱")

    assert report.status.value == "report_ready"
    assert report.action.value == "watch"
    assert report.confidence.value == "medium"
    assert report.summary
    assert report.task_id.startswith("analysis-")
    assert report.risk_controls is not None
    assert report.investment_plan is not None
    assert report.investment_plan.direction.value == "watch"
    assert report.data_trust is not None
    assert report.engine_telemetry is not None
    assert report.engine_cost_guardrail is not None
    assert report.agent_views[0].agent == "Quick Agent"
    assert report.engine_source == "quick-agent"
    assert report.data_context.events[0].event_type.value == "earnings_forecast"
    assert report.data_context.events[0].priority == "high"
    assert service.get_report(report.task_id) == report


def test_high_priority_risk_events_push_plan_to_wait() -> None:
    service = AnalysisService(
        resolver=StockResolver(name_map={"贵州茅台": "600519"}),
        context_builder=DataContextBuilder(
            StaticMarketDataProvider(
                quote={"price": 1688.0},
                technicals={"ma5": 1660.0},
                fundamentals={"pe_ttm": 28.5},
                news=[{"title": "控股股东股权质押进展公告", "content": "质押比例上升"}],
            )
        ),
        quick_router=QuickAgentRouter(),
        deep_engine=MockDeepResearchEngine(),
    )

    report = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议")

    assert report.investment_plan is not None
    assert report.investment_plan.direction.value == "wait"
    assert report.investment_plan.target_position_pct == 0.0
    assert any("高优先级风险事件占优" in text for text in report.investment_plan.rationale)
    assert any(
        "高优先级事件证据覆盖" in text
        or "高优先级事件主要来自正文命中" in text
        or "高优先级事件主要来自标题命中" in text
        or "高优先级事件主要来自标题与正文" in text
        for text in report.investment_plan.rationale
    )
    assert any("风险事件占优" in text for text in report.investment_plan.risk_notes)
    assert any("正文命中已进入计划解释" in text or "当前高优先级信号主要来自标题" in text for text in report.investment_plan.risk_notes)


def test_high_priority_positive_events_push_plan_to_buy() -> None:
    service = AnalysisService(
        resolver=StockResolver(name_map={"贵州茅台": "600519"}),
        context_builder=DataContextBuilder(
            StaticMarketDataProvider(
                quote={"price": 1688.0},
                technicals={"ma5": 1660.0},
                fundamentals={"pe_ttm": 28.5},
                news=[{"title": "控股股东拟增持公司股份", "content": "计划在未来 6 个月内增持不超过 2% 股份"}],
            )
        ),
        quick_router=QuickAgentRouter(),
        deep_engine=MockDeepResearchEngine(),
    )

    report = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议")

    assert report.investment_plan is not None
    assert report.investment_plan.direction.value == "buy"
    assert report.investment_plan.target_position_pct == report.risk_controls.max_position_pct
    assert any("高优先级正向事件占优" in text for text in report.investment_plan.rationale)
    assert any(
        "高优先级事件证据覆盖" in text
        or "高优先级事件主要来自正文命中" in text
        or "高优先级事件主要来自标题命中" in text
        or "高优先级事件主要来自标题与正文" in text
        for text in report.investment_plan.rationale
    )


def test_create_single_stock_analysis_saves_report_to_repository() -> None:
    repository = InMemoryAnalysisReportRepository()
    service = build_service(repository=repository)

    report = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议")

    assert repository.get(report.task_id) == report
    assert service.get_report(report.task_id) == report


def test_list_reports_returns_repository_records() -> None:
    repository = InMemoryAnalysisReportRepository()
    service = build_service(repository=repository)
    report = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议")

    records = service.list_reports(limit=10)

    assert records[0].task_id == report.task_id
