"""Deterministic risk discipline for analysis reports."""

from dataclasses import replace

from money_api.domains.analysis.contracts import (
    AnalysisReport,
    AnalysisStatus,
    ConfidenceLevel,
    DecisionAction,
    RiskControlPlan,
    RiskControlRule,
)


DISCLAIMER = "本报告仅用于研究和复盘，不构成投资建议；任何交易决策需由用户自行承担风险。"


class DefaultRiskPolicy:
    def evaluate(self, report: AnalysisReport) -> RiskControlPlan:
        max_position_pct = self._base_position(report.confidence)
        rules = [
            RiskControlRule(
                name="confidence",
                level=report.confidence.value,
                message=f"基于 {report.confidence.value} 置信度设定初始仓位上限。",
            )
        ]

        if report.data_context.gaps:
            max_position_pct = min(max_position_pct, 0.05)
            rules.append(
                RiskControlRule(
                    name="data_gaps",
                    level="medium",
                    message="存在数据缺口，仓位上限降至 5%。",
                )
            )

        if report.action == DecisionAction.WAIT:
            max_position_pct = min(max_position_pct, 0.03)
            rules.append(RiskControlRule(name="action", level="low", message="等待动作仅允许观察仓位。"))

        if report.action == DecisionAction.SELL:
            max_position_pct = 0
            rules.append(RiskControlRule(name="action", level="high", message="卖出动作不允许新增仓位。"))

        if report.status == AnalysisStatus.FAILED:
            max_position_pct = 0
            rules.append(RiskControlRule(name="status", level="high", message="分析失败，不允许建立仓位。"))

        return RiskControlPlan(
            max_position_pct=max_position_pct,
            stop_loss_pct=0.08,
            take_profit_pct=0.15,
            time_horizon="5-20 个交易日",
            rules=rules,
            disclaimer=DISCLAIMER,
        )

    def apply(self, report: AnalysisReport) -> AnalysisReport:
        return replace(report, risk_controls=self.evaluate(report))

    def _base_position(self, confidence: ConfidenceLevel) -> float:
        if confidence == ConfidenceLevel.HIGH:
            return 0.2
        if confidence == ConfidenceLevel.MEDIUM:
            return 0.1
        return 0.05
