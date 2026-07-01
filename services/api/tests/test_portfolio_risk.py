from dataclasses import replace

from money_api.domains.analysis.contracts import (
    AnalysisReport,
    AnalysisStatus,
    ConfidenceLevel,
    DataContext,
    DecisionAction,
    RiskControlPlan,
    StockIdentity,
)
from money_api.domains.analysis.portfolio_risk import PortfolioRiskBudgeter
from money_api.domains.analysis.risk_policy import DefaultRiskPolicy


def build_report(
    code: str,
    *,
    action: DecisionAction = DecisionAction.WATCH,
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
    max_position_pct: float | None = None,
) -> AnalysisReport:
    stock = StockIdentity(code=code, name=f"股票{code}")
    report = AnalysisReport(
        task_id=f"task-{code}",
        stock=stock,
        status=AnalysisStatus.REPORT_READY,
        action=action,
        confidence=confidence,
        summary="summary",
        reasons=[],
        risks=[],
        agent_views=[],
        data_context=DataContext(stock=stock),
    )
    controlled = DefaultRiskPolicy().apply(report)
    if max_position_pct is None:
        return controlled
    assert controlled.risk_controls is not None
    return replace(
        controlled,
        risk_controls=RiskControlPlan(
            max_position_pct=max_position_pct,
            stop_loss_pct=controlled.risk_controls.stop_loss_pct,
            take_profit_pct=controlled.risk_controls.take_profit_pct,
            time_horizon=controlled.risk_controls.time_horizon,
            rules=controlled.risk_controls.rules,
            disclaimer=controlled.risk_controls.disclaimer,
        ),
    )


def test_portfolio_budget_uses_report_risk_controls() -> None:
    budget = PortfolioRiskBudgeter(max_total_position_pct=0.6).build(
        [build_report("600519", max_position_pct=0.1), build_report("000001", max_position_pct=0.2)]
    )

    assert budget.total_position_pct == 0.3
    assert budget.cash_reserve_pct == 0.7
    assert [position.stock.code for position in budget.positions] == ["600519", "000001"]
    assert [position.budget_position_pct for position in budget.positions] == [0.1, 0.2]


def test_portfolio_budget_scales_down_when_total_exceeds_cap() -> None:
    budget = PortfolioRiskBudgeter(max_total_position_pct=0.3, max_single_position_pct=0.2).build(
        [build_report("600519", max_position_pct=0.2), build_report("000001", max_position_pct=0.2)]
    )

    assert budget.total_position_pct == 0.3
    assert [position.budget_position_pct for position in budget.positions] == [0.15, 0.15]
    assert any(rule.name == "total_position_cap" for rule in budget.rules)


def test_portfolio_budget_blocks_reports_without_risk_controls() -> None:
    raw_report = build_report("600519")
    report_without_controls = replace(raw_report, risk_controls=None)

    budget = PortfolioRiskBudgeter().build([report_without_controls])

    assert budget.total_position_pct == 0
    assert budget.positions[0].budget_position_pct == 0
    assert any(rule.name == "missing_risk_controls" for rule in budget.positions[0].rules)


def test_portfolio_budget_handles_empty_reports() -> None:
    budget = PortfolioRiskBudgeter().build([])

    assert budget.total_position_pct == 0
    assert budget.cash_reserve_pct == 1
    assert budget.positions == []
    assert any(rule.name == "empty_portfolio" for rule in budget.rules)
