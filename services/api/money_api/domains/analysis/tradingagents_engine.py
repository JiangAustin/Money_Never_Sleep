"""TradingAgents engine adapter contracts."""

from dataclasses import dataclass, field, replace
from datetime import date
from typing import Any, Protocol

from money_api.domains.analysis.agent_engine import MockDeepResearchEngine
from money_api.domains.analysis.contracts import (
    AgentView,
    AnalysisReport,
    AnalysisStatus,
    ConfidenceLevel,
    DataContext,
    DecisionAction,
    RiskFinding,
)


_ACTION_MAP = {
    "BUY": DecisionAction.BUY,
    "WATCH": DecisionAction.WATCH,
    "HOLD": DecisionAction.WATCH,
    "WAIT": DecisionAction.WAIT,
    "SELL": DecisionAction.SELL,
}


@dataclass(frozen=True)
class TradingAgentsRunRequest:
    task_id: str
    code: str
    name: str
    market: str
    trade_date: str
    context_snapshot: dict[str, Any]
    diagnostics: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_context(cls, task_id: str, context: DataContext, trade_date: str | None = None) -> "TradingAgentsRunRequest":
        return cls(
            task_id=task_id,
            code=context.stock.code,
            name=context.stock.name,
            market=context.stock.market,
            trade_date=trade_date or date.today().isoformat(),
            context_snapshot={
                "quote": dict(context.quote),
                "technicals": dict(context.technicals),
                "fundamentals": dict(context.fundamentals),
                "news": list(context.news),
                "gaps": list(context.gaps),
            },
            diagnostics=list(context.diagnostics),
        )


@dataclass(frozen=True)
class TradingAgentsRunResult:
    ok: bool
    source: str
    final_decision: str = "WATCH"
    summary: str = ""
    agent_reports: dict[str, str] = field(default_factory=dict)
    raw_state: dict[str, Any] = field(default_factory=dict)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    error_type: str | None = None
    error_message: str | None = None


class TradingAgentsRunner(Protocol):
    def run(self, request: TradingAgentsRunRequest) -> TradingAgentsRunResult: ...


class FakeTradingAgentsRunner:
    def run(self, request: TradingAgentsRunRequest) -> TradingAgentsRunResult:
        return TradingAgentsRunResult(
            ok=True,
            source="fake-tradingagents",
            final_decision="WATCH",
            summary=f"{request.name} fake TradingAgents 分析完成。",
            agent_reports={
                "market": "离线市场分析结果",
                "fundamentals": "离线基本面分析结果",
                "risk": "离线风险辩论结果",
            },
            diagnostics=[{"kind": "deep_engine", "source": "fake-tradingagents", "ok": True}],
        )


class TradingAgentsDeepResearchEngine:
    def __init__(self, runner: TradingAgentsRunner, trade_date: str | None = None):
        self.runner = runner
        self.trade_date = trade_date

    def analyze(self, task_id: str, context: DataContext) -> AnalysisReport:
        request = TradingAgentsRunRequest.from_context(task_id, context, self.trade_date)
        result = self.runner.run(request)
        diagnostics = list(context.diagnostics) + list(result.diagnostics)
        report_context = DataContext(
            stock=context.stock,
            quote=dict(context.quote),
            technicals=dict(context.technicals),
            fundamentals=dict(context.fundamentals),
            news=list(context.news),
            gaps=list(context.gaps),
            diagnostics=diagnostics,
        )
        if result.ok:
            return AnalysisReport(
                task_id=task_id,
                stock=context.stock,
                status=AnalysisStatus.REPORT_READY,
                action=_ACTION_MAP.get(result.final_decision.upper(), DecisionAction.WATCH),
                confidence=ConfidenceLevel.LOW if context.gaps else ConfidenceLevel.MEDIUM,
                summary=result.summary,
                reasons=["TradingAgents 深度投研引擎已返回结果"],
                risks=[RiskFinding(level="low", message="真实引擎输出仍需人工复核")],
                agent_views=[
                    AgentView(agent=f"TradingAgents {name}", conclusion=report)
                    for name, report in result.agent_reports.items()
                ],
                data_context=report_context,
            )
        return self._failed_report(task_id, context, result, report_context)

    def _failed_report(
        self,
        task_id: str,
        context: DataContext,
        result: TradingAgentsRunResult,
        report_context: DataContext,
    ) -> AnalysisReport:
        message = result.error_message or "unknown error"
        return AnalysisReport(
            task_id=task_id,
            stock=context.stock,
            status=AnalysisStatus.FAILED,
            action=DecisionAction.WATCH,
            confidence=ConfidenceLevel.LOW,
            summary="TradingAgents 深度投研引擎执行失败。",
            reasons=["TradingAgents runner 返回失败结果"],
            risks=[RiskFinding(level="high", message=f"TradingAgents 执行失败: {message}")],
            agent_views=[AgentView(agent="TradingAgents", conclusion="真实深度投研未完成")],
            data_context=report_context,
        )


class AutoFallbackDeepResearchEngine:
    def __init__(self, primary: TradingAgentsDeepResearchEngine, fallback: MockDeepResearchEngine | None = None):
        self.primary = primary
        self.fallback = fallback or MockDeepResearchEngine()

    def analyze(self, task_id: str, context: DataContext) -> AnalysisReport:
        primary_report = self.primary.analyze(task_id, context)
        if primary_report.status != AnalysisStatus.FAILED:
            return primary_report

        diagnostics = list(primary_report.data_context.diagnostics)
        diagnostics.append(
            {
                "kind": "deep_engine",
                "source": "mock-fallback",
                "ok": True,
                "error_type": primary_report.data_context.diagnostics[-1].get("error_type") if primary_report.data_context.diagnostics else None,
                "error_message": primary_report.data_context.diagnostics[-1].get("error_message") if primary_report.data_context.diagnostics else None,
                "fetched_at": None,
                "is_stale": False,
            }
        )
        fallback_context = DataContext(
            stock=context.stock,
            quote=dict(context.quote),
            technicals=dict(context.technicals),
            fundamentals=dict(context.fundamentals),
            news=list(context.news),
            gaps=list(context.gaps),
            diagnostics=diagnostics,
        )
        fallback_report = self.fallback.analyze(task_id, fallback_context)
        return replace(
            fallback_report,
            summary="TradingAgents 不可用，已回退到 mock 分析。",
            reasons=["TradingAgents auto 模式失败后已回退到 mock 分析", *fallback_report.reasons],
        )
