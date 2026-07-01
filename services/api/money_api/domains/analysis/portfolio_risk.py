"""Portfolio-level risk budget calculation."""

from money_api.domains.analysis.contracts import (
    AnalysisReport,
    PortfolioPositionBudget,
    PortfolioRiskBudget,
    RiskControlRule,
)
from money_api.domains.analysis.risk_policy import DISCLAIMER


class PortfolioRiskBudgeter:
    def __init__(self, max_total_position_pct: float = 0.6, max_single_position_pct: float = 0.2):
        self.max_total_position_pct = max_total_position_pct
        self.max_single_position_pct = max_single_position_pct

    def build(self, reports: list[AnalysisReport]) -> PortfolioRiskBudget:
        if not reports:
            return PortfolioRiskBudget(
                total_position_pct=0,
                cash_reserve_pct=1,
                max_total_position_pct=self.max_total_position_pct,
                max_single_position_pct=self.max_single_position_pct,
                positions=[],
                rules=[RiskControlRule(name="empty_portfolio", level="low", message="没有可纳入组合预算的报告。")],
                disclaimer=DISCLAIMER,
            )

        positions = [self._position_from_report(report) for report in reports]
        source_total = sum(position.budget_position_pct for position in positions)
        rules = [
            RiskControlRule(
                name="single_position_cap",
                level="medium",
                message=f"单一标的预算不超过 {self.max_single_position_pct:.0%}。",
            )
        ]
        if source_total > self.max_total_position_pct and source_total > 0:
            scale = self.max_total_position_pct / source_total
            positions = [
                PortfolioPositionBudget(
                    task_id=position.task_id,
                    stock=position.stock,
                    action=position.action,
                    confidence=position.confidence,
                    budget_position_pct=round(position.budget_position_pct * scale, 6),
                    source_position_pct=position.source_position_pct,
                    rules=position.rules
                    + [
                        RiskControlRule(
                            name="scaled_by_total_cap",
                            level="medium",
                            message="组合总仓位超过上限，按比例压缩该标的预算。",
                        )
                    ],
                )
                for position in positions
            ]
            rules.append(
                RiskControlRule(
                    name="total_position_cap",
                    level="medium",
                    message=f"组合总仓位上限为 {self.max_total_position_pct:.0%}，已按比例压缩。",
                )
            )
        else:
            rules.append(
                RiskControlRule(
                    name="total_position_cap",
                    level="low",
                    message=f"组合总仓位不超过 {self.max_total_position_pct:.0%}。",
                )
            )

        total_position_pct = round(sum(position.budget_position_pct for position in positions), 6)
        return PortfolioRiskBudget(
            total_position_pct=total_position_pct,
            cash_reserve_pct=round(max(0, 1 - total_position_pct), 6),
            max_total_position_pct=self.max_total_position_pct,
            max_single_position_pct=self.max_single_position_pct,
            positions=positions,
            rules=rules,
            disclaimer=DISCLAIMER,
        )

    def _position_from_report(self, report: AnalysisReport) -> PortfolioPositionBudget:
        if report.risk_controls is None:
            return PortfolioPositionBudget(
                task_id=report.task_id,
                stock=report.stock,
                action=report.action,
                confidence=report.confidence,
                budget_position_pct=0,
                source_position_pct=0,
                rules=[
                    RiskControlRule(
                        name="missing_risk_controls",
                        level="high",
                        message="报告缺少风控计划，不纳入组合仓位。",
                    )
                ],
            )

        source_position_pct = max(0, report.risk_controls.max_position_pct)
        budget_position_pct = min(source_position_pct, self.max_single_position_pct)
        rules = list(report.risk_controls.rules)
        if budget_position_pct < source_position_pct:
            rules.append(
                RiskControlRule(
                    name="single_position_cap",
                    level="medium",
                    message="单票仓位超过组合单票上限，已压缩。",
                )
            )
        return PortfolioPositionBudget(
            task_id=report.task_id,
            stock=report.stock,
            action=report.action,
            confidence=report.confidence,
            budget_position_pct=round(budget_position_pct, 6),
            source_position_pct=round(source_position_pct, 6),
            rules=rules,
        )
