"""Agent engine abstractions for analysis orchestration."""

from typing import Protocol

from money_api.domains.analysis.contracts import (
    AgentView,
    AnalysisReport,
    AnalysisStatus,
    ConfidenceLevel,
    DataContext,
    DecisionAction,
    RiskFinding,
)


class DeepResearchEngine(Protocol):
    def analyze(self, task_id: str, context: DataContext) -> AnalysisReport: ...


class QuickAgentRouter:
    deep_keywords = ("全面分析", "深度分析", "投资建议", "操作建议", "风险评估")

    def needs_deep_analysis(self, message: str) -> bool:
        """Return True when message contains any deep-analysis keyword substring."""
        if not isinstance(message, str) or not message:
            return False
        return any(keyword in message for keyword in self.deep_keywords)


class MockDeepResearchEngine:
    """Dry-run engine for contract validation, not real investment research output."""

    def analyze(self, task_id: str, context: DataContext) -> AnalysisReport:
        confidence = ConfidenceLevel.LOW if context.gaps else ConfidenceLevel.MEDIUM
        risks = [RiskFinding(level="medium", message=f"数据缺口: {gap}") for gap in context.gaps]
        if not risks:
            risks = [RiskFinding(level="low", message="当前为 mock 分析，需接入真实投研引擎验证")]
        return AnalysisReport(
            task_id=task_id,
            stock=context.stock,
            status=AnalysisStatus.REPORT_READY,
            action=DecisionAction.WATCH,
            confidence=confidence,
            summary="当前为平台骨架 dry run，结论仅用于验证分析契约。",
            reasons=["已完成数据上下文构建", "已通过 Agent 引擎适配器生成报告"],
            risks=risks,
            agent_views=[AgentView(agent="Mock Research Engine", conclusion="等待真实深度投研引擎接入")],
            data_context=context,
        )