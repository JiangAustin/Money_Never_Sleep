"""Application service for single-stock analysis dry runs."""

from dataclasses import replace
from uuid import uuid4

from money_api.domains.analysis.agent_engine import DeepResearchEngine, QuickAgentRouter
from money_api.domains.analysis.backtest import SimpleBacktestEngine
from money_api.domains.analysis.context_builder import DataContextBuilder
from money_api.domains.analysis.contracts import (
    AgentView,
    AnalysisReport,
    AnalysisStatus,
    BacktestOptions,
    BacktestPricePoint,
    BacktestResult,
    ConfidenceLevel,
    DecisionAction,
    DataTrustScore,
    EngineCostGuardrail,
    EngineTelemetry,
    InvestmentPlan,
    MarketEvent,
    MarketEventType,
    PortfolioRiskBudget,
    RiskFinding,
)
from money_api.domains.analysis.portfolio_risk import PortfolioRiskBudgeter
from money_api.domains.analysis.report_repository import (
    AnalysisReportRecord,
    AnalysisReportRepository,
    InMemoryAnalysisReportRepository,
)
from money_api.domains.analysis.provenance import collect_data_sources
from money_api.domains.analysis.risk_policy import DefaultRiskPolicy
from money_api.domains.market_data.provider_results import ProviderResult
from money_api.domains.market_data.resolver import StockResolver
from time import perf_counter


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
        portfolio_budgeter: PortfolioRiskBudgeter | None = None,
    ):
        self.resolver = resolver
        self.context_builder = context_builder
        self.quick_router = quick_router
        self.deep_engine = deep_engine
        self.report_repository = report_repository or InMemoryAnalysisReportRepository()
        self.risk_policy = risk_policy or DefaultRiskPolicy()
        self.backtest_engine = backtest_engine or SimpleBacktestEngine()
        self.portfolio_budgeter = portfolio_budgeter or PortfolioRiskBudgeter()

    def create_single_stock_analysis(self, symbol: str, message: str) -> AnalysisReport:
        started_at = perf_counter()
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
                engine_source="quick-agent",
                engine_mode="quick-screening",
            )
        report = replace(report, data_sources=collect_data_sources(report.data_context.diagnostics))
        report = self.risk_policy.apply(report)
        report = replace(report, data_trust=DataTrustScore.from_report(report))
        report = replace(report, investment_plan=self._build_investment_plan(report))
        runtime_ms = int((perf_counter() - started_at) * 1000)
        report = replace(report, engine_telemetry=EngineTelemetry.from_report(report, runtime_ms))
        report = replace(report, engine_cost_guardrail=EngineCostGuardrail.from_telemetry(report.engine_telemetry))
        self.report_repository.save(report)
        return report

    def get_report(self, task_id: str) -> AnalysisReport | None:
        return self.report_repository.get(task_id)

    def list_reports(self, limit: int = 20) -> list[AnalysisReportRecord]:
        return self.report_repository.list_recent(limit=limit)

    def backtest_report(self, task_id: str, prices: list[BacktestPricePoint], options: BacktestOptions | None = None) -> BacktestResult | None:
        report = self.get_report(task_id)
        if report is None:
            return None
        return self.backtest_engine.run(report, prices, options=options)

    def backtest_report_from_provider(self, task_id: str, provider, limit: int = 60, options: BacktestOptions | None = None) -> BacktestResult | None:
        report = self.get_report(task_id)
        if report is None:
            return None
        result: ProviderResult = provider.get_price_series(report.stock, limit=limit)
        if not result.ok:
            raise ValueError(result.error_message or "price series provider failed")
        return self.backtest_engine.run(report, list(result.data), options=options)

    def build_portfolio_risk_budget(self, task_ids: list[str] | None = None, limit: int = 20) -> PortfolioRiskBudget:
        if task_ids:
            reports = [report for task_id in task_ids if (report := self.get_report(task_id)) is not None]
        else:
            reports = [AnalysisReport.from_dict(record.report) for record in self.list_reports(limit=limit)]
        return self.portfolio_budgeter.build(reports)

    def _build_investment_plan(self, report: AnalysisReport) -> InvestmentPlan:
        risk_controls = report.risk_controls
        max_position_pct = risk_controls.max_position_pct if risk_controls is not None else 0.05
        stop_loss_pct = risk_controls.stop_loss_pct if risk_controls is not None else 0.08
        take_profit_pct = risk_controls.take_profit_pct if risk_controls is not None else 0.15
        observation_window = risk_controls.time_horizon if risk_controls is not None else "5-20 个交易日"
        rationale = list(report.reasons[:3]) or [report.summary]
        risk_notes = [risk.message for risk in report.risks] or ["当前报告未包含额外风险提示"]
        event_signal = self._summarize_event_signal(list(report.data_context.events))
        if event_signal["summary"]:
            rationale.append(event_signal["summary"])
        if event_signal["evidence_summary"]:
            rationale.append(event_signal["evidence_summary"])
        if event_signal["risk_note"]:
            risk_notes.append(event_signal["risk_note"])
        if event_signal["evidence_note"]:
            risk_notes.append(event_signal["evidence_note"])

        if report.engine_mode != "quick-screening" and event_signal["positive_count"] > event_signal["negative_count"] and event_signal["positive_count"] > 0:
            direction = DecisionAction.BUY if report.action != DecisionAction.SELL else DecisionAction.SELL
        elif report.engine_mode != "quick-screening" and event_signal["negative_count"] > event_signal["positive_count"] and event_signal["negative_count"] > 0:
            direction = DecisionAction.WAIT if report.action != DecisionAction.SELL else DecisionAction.SELL
        else:
            direction = report.action

        if direction == DecisionAction.BUY:
            entry_conditions = ["价格确认站稳后再分批介入"]
            exit_conditions = ["跌破止损线", "核心事件逻辑失效", "目标收益达到"]
            review_conditions = ["每个交易日收盘后复核", "新增结构化事件后立即复核"]
            target_position_pct = max_position_pct
        elif direction == DecisionAction.SELL:
            entry_conditions = ["仅在反弹失败后执行减仓"]
            exit_conditions = ["风险事件继续恶化", "下行趋势确认"]
            review_conditions = ["盘后复核风险暴露", "重大公告后复核"]
            target_position_pct = 0.0
        elif direction == DecisionAction.WAIT:
            entry_conditions = ["等待更明确的趋势或事件确认"]
            exit_conditions = ["不满足入场条件", "证据仍不足以形成有效计划"]
            review_conditions = ["每日复核一次", "新的高置信事件出现时复核"]
            target_position_pct = 0.0
        else:
            entry_conditions = ["维持观察仓位，不主动追高"]
            exit_conditions = ["跌破止损线", "风险回升或逻辑变化"]
            review_conditions = ["盘后复核一次", "当日新增事件触发时复核"]
            if event_signal["positive_count"] > 0 and event_signal["negative_count"] == 0 and report.engine_mode != "quick-screening":
                target_position_pct = max_position_pct
            elif event_signal["negative_count"] > 0 and event_signal["positive_count"] == 0 and report.engine_mode != "quick-screening":
                target_position_pct = 0.0
            elif event_signal["positive_count"] > 0 and event_signal["negative_count"] > 0 and report.engine_mode != "quick-screening":
                target_position_pct = max_position_pct * 0.5
            else:
                target_position_pct = max_position_pct

        return InvestmentPlan(
            direction=direction,
            target_position_pct=target_position_pct,
            entry_conditions=entry_conditions,
            exit_conditions=exit_conditions,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            observation_window=observation_window,
            review_conditions=review_conditions,
            rationale=rationale,
            risk_notes=risk_notes,
        )

    def _summarize_event_signal(self, events: list[MarketEvent]) -> dict[str, object]:
        positive_types = {MarketEventType.EARNINGS_FORECAST, MarketEventType.SHARE_REPURCHASE, MarketEventType.SHARE_INCREASE}
        negative_types = {MarketEventType.SHARE_REDUCTION, MarketEventType.GUARANTEE, MarketEventType.SHARE_PLEDGE}
        high_priority_events = [event for event in events if getattr(event, "priority", "medium") == "high"]
        positive_count = sum(1 for event in high_priority_events if event.event_type in positive_types)
        negative_count = sum(1 for event in high_priority_events if event.event_type in negative_types)
        title_count = sum(1 for event in high_priority_events if getattr(event, "evidence_scope", "") == "title")
        content_count = sum(1 for event in high_priority_events if getattr(event, "evidence_scope", "") == "content")
        mixed_count = sum(1 for event in high_priority_events if getattr(event, "evidence_scope", "") == "title+content")
        evidence_summary = ""
        evidence_note = ""
        if mixed_count > 0:
            evidence_summary = f"高优先级事件证据覆盖标题与正文 {mixed_count} 条。"
        elif content_count > 0:
            evidence_summary = f"高优先级事件主要来自正文命中 {content_count} 条。"
        elif title_count > 0:
            evidence_summary = f"高优先级事件主要来自标题命中 {title_count} 条。"
        if content_count > 0:
            evidence_note = "正文命中已进入计划解释，说明公告/资讯正文正在提供可复核信号。"
        elif mixed_count > 0:
            evidence_note = "标题与正文同时命中的事件较多，说明研究信号解释性较强。"
        elif title_count > 0:
            evidence_note = "当前高优先级信号主要来自标题，后续需要继续观察正文是否补强。"
        if positive_count > negative_count and positive_count > 0:
            return {
                "positive_count": positive_count,
                "negative_count": negative_count,
                "summary": f"高优先级正向事件占优：{positive_count} 条。",
                "risk_note": "正向事件占优，可提升计划激进度，但仍需结合风险控制。",
                "evidence_summary": evidence_summary,
                "evidence_note": evidence_note,
            }
        if negative_count > positive_count and negative_count > 0:
            return {
                "positive_count": positive_count,
                "negative_count": negative_count,
                "summary": f"高优先级风险事件占优：{negative_count} 条。",
                "risk_note": "风险事件占优，计划应收缩到观察或退出。",
                "evidence_summary": evidence_summary,
                "evidence_note": evidence_note,
            }
        if positive_count > 0 and negative_count > 0:
            return {
                "positive_count": positive_count,
                "negative_count": negative_count,
                "summary": f"高优先级正负事件并存：正向 {positive_count} 条、风险 {negative_count} 条。",
                "risk_note": "正负事件并存，建议保持中性仓位并密切复核。",
                "evidence_summary": evidence_summary,
                "evidence_note": evidence_note,
            }
        if positive_count > 0:
            return {
                "positive_count": positive_count,
                "negative_count": negative_count,
                "summary": f"高优先级正向事件 {positive_count} 条。",
                "risk_note": "",
                "evidence_summary": evidence_summary,
                "evidence_note": evidence_note,
            }
        if negative_count > 0:
            return {
                "positive_count": positive_count,
                "negative_count": negative_count,
                "summary": f"高优先级风险事件 {negative_count} 条。",
                "risk_note": "",
                "evidence_summary": evidence_summary,
                "evidence_note": evidence_note,
            }
        return {
            "positive_count": 0,
            "negative_count": 0,
            "summary": "",
            "risk_note": "",
            "evidence_summary": evidence_summary,
            "evidence_note": evidence_note,
        }
