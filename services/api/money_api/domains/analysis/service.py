"""Application service for single-stock analysis dry runs."""

from uuid import uuid4

from money_api.domains.analysis.agent_engine import DeepResearchEngine, QuickAgentRouter
from money_api.domains.analysis.backtest import SimpleBacktestEngine
from money_api.domains.analysis.context_builder import DataContextBuilder
from money_api.domains.analysis.contracts import (
    AgentView,
    AnalysisReport,
    AnalysisStatus,
    BacktestPricePoint,
    BacktestResult,
    ConfidenceLevel,
    DecisionAction,
    RiskFinding,
)
from money_api.domains.analysis.report_repository import (
    AnalysisReportRecord,
    AnalysisReportRepository,
    InMemoryAnalysisReportRepository,
)
from money_api.domains.analysis.risk_policy import DefaultRiskPolicy
from money_api.domains.market_data.resolver import StockResolver


class AnalysisService:
    def __init__(
        self,
        resolver: StockResolver,
        context_builder: DataContextBuilder,
        quick_router: QuickAgentRouter,
        deep_engine: DeepResearchEngine,
        report_repository: AnalysisReportRepository | None = None,
        risk_policy: DefaultRiskPolicy | None = None,
        backtest_engine: SimpleBacktestEngine | None = None,
    ):
        self.resolver = resolver
        self.context_builder = context_builder
        self.quick_router = quick_router
        self.deep_engine = deep_engine
        self.report_repository = report_repository or InMemoryAnalysisReportRepository()
        self.risk_policy = risk_policy or DefaultRiskPolicy()
        self.backtest_engine = backtest_engine or SimpleBacktestEngine()

    def create_single_stock_analysis(self, symbol: str, message: str) -> AnalysisReport:
        task_id = f"analysis-{uuid4().hex}"
        stock = self.resolver.resolve(symbol)
        context = self.context_builder.build(stock)
        if self.quick_router.needs_deep_analysis(message):
            report = self.deep_engine.analyze(task_id, context)
        else:
            report = AnalysisReport(
                task_id=task_id,
                stock=stock,
                status=AnalysisStatus.REPORT_READY,
                action=DecisionAction.WATCH,
                confidence=ConfidenceLevel.LOW if context.gaps else ConfidenceLevel.MEDIUM,
                summary="轻量查询已完成，未触发完整深度投研流程。",
                reasons=["问题属于轻量查询，无需完整投研", "已获取统一数据上下文"],
                risks=[RiskFinding(level="low", message="轻量结论不构成完整投资建议")],
                agent_views=[AgentView(agent="Quick Agent", conclusion="返回轻量分析摘要")],
                data_context=context,
            )
        report = self.risk_policy.apply(report)
        self.report_repository.save(report)
        return report

    def get_report(self, task_id: str) -> AnalysisReport | None:
        return self.report_repository.get(task_id)

    def list_reports(self, limit: int = 20) -> list[AnalysisReportRecord]:
        return self.report_repository.list_recent(limit=limit)

    def backtest_report(self, task_id: str, prices: list[BacktestPricePoint]) -> BacktestResult | None:
        report = self.get_report(task_id)
        if report is None:
            return None
        return self.backtest_engine.run(report, prices)