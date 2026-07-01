from money_api.domains.analysis.contracts import (
    AnalysisReport,
    AnalysisStatus,
    ConfidenceLevel,
    DataContext,
    DecisionAction,
    StockIdentity,
)
from money_api.domains.analysis.risk_policy import DefaultRiskPolicy


def build_report(
    *,
    status: AnalysisStatus = AnalysisStatus.REPORT_READY,
    action: DecisionAction = DecisionAction.WATCH,
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
    gaps: list[str] | None = None,
) -> AnalysisReport:
    stock = StockIdentity(code="600519", name="贵州茅台")
    return AnalysisReport(
        task_id="task-1",
        stock=stock,
        status=status,
        action=action,
        confidence=confidence,
        summary="summary",
        reasons=[],
        risks=[],
        agent_views=[],
        data_context=DataContext(stock=stock, gaps=gaps or []),
    )


def test_medium_confidence_allows_ten_percent_position() -> None:
    plan = DefaultRiskPolicy().evaluate(build_report(confidence=ConfidenceLevel.MEDIUM))

    assert plan.max_position_pct == 0.1
    assert plan.stop_loss_pct == 0.08
    assert plan.take_profit_pct == 0.15
    assert plan.disclaimer


def test_low_confidence_caps_position() -> None:
    plan = DefaultRiskPolicy().evaluate(build_report(confidence=ConfidenceLevel.LOW))

    assert plan.max_position_pct == 0.05


def test_data_gaps_cap_position_and_add_rule() -> None:
    plan = DefaultRiskPolicy().evaluate(build_report(confidence=ConfidenceLevel.HIGH, gaps=["news"]))

    assert plan.max_position_pct == 0.05
    assert any(rule.name == "data_gaps" for rule in plan.rules)


def test_failed_report_blocks_position() -> None:
    plan = DefaultRiskPolicy().evaluate(build_report(status=AnalysisStatus.FAILED))

    assert plan.max_position_pct == 0
    assert any(rule.name == "status" and rule.level == "high" for rule in plan.rules)


def test_sell_action_blocks_position() -> None:
    plan = DefaultRiskPolicy().evaluate(build_report(action=DecisionAction.SELL, confidence=ConfidenceLevel.HIGH))

    assert plan.max_position_pct == 0


def test_apply_returns_report_with_risk_controls() -> None:
    report = build_report()

    controlled = DefaultRiskPolicy().apply(report)

    assert controlled.risk_controls is not None
    assert controlled.risk_controls.max_position_pct == 0.1
