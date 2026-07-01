import pytest

from money_api.domains.analysis.backtest import SimpleBacktestEngine
from money_api.domains.analysis.contracts import (
    AnalysisReport,
    AnalysisStatus,
    BacktestPricePoint,
    BacktestOptions,
    ConfidenceLevel,
    DataContext,
    DecisionAction,
    RiskControlPlan,
    StockIdentity,
)


def build_report() -> AnalysisReport:
    stock = StockIdentity(code="600519", name="贵州茅台")
    return AnalysisReport(
        task_id="task-1",
        stock=stock,
        status=AnalysisStatus.REPORT_READY,
        action=DecisionAction.WATCH,
        confidence=ConfidenceLevel.MEDIUM,
        summary="summary",
        reasons=[],
        risks=[],
        agent_views=[],
        data_context=DataContext(stock=stock),
        risk_controls=RiskControlPlan(
            max_position_pct=0.1,
            stop_loss_pct=0.08,
            take_profit_pct=0.15,
            time_horizon="5-20 个交易日",
            rules=[],
            disclaimer="非投资建议",
        ),
    )


def prices(*values: float) -> list[BacktestPricePoint]:
    return [BacktestPricePoint(date=f"2026-07-{index + 1:02d}", close=value) for index, value in enumerate(values)]


def test_backtest_take_profit() -> None:
    result = SimpleBacktestEngine().run(build_report(), prices(100, 108, 116, 120))

    assert result.exit_reason == "take_profit"
    assert result.exit_price == 116
    assert result.return_pct == 0.16
    assert result.holding_days == 2


def test_backtest_stop_loss() -> None:
    result = SimpleBacktestEngine().run(build_report(), prices(100, 96, 91, 88))

    assert result.exit_reason == "stop_loss"
    assert result.exit_price == 91
    assert result.return_pct == -0.09


def test_backtest_time_exit_and_drawdown() -> None:
    result = SimpleBacktestEngine().run(build_report(), prices(100, 98, 105, 103))

    assert result.exit_reason == "time_exit"
    assert result.exit_price == 103
    assert result.return_pct == 0.03
    assert result.gross_return_pct == 0.03
    assert result.cost_impact_pct == 0
    assert result.max_drawdown_pct == -0.02


def test_backtest_applies_costs_and_slippage_to_net_return() -> None:
    result = SimpleBacktestEngine().run(
        build_report(),
        prices(100, 112),
        options=BacktestOptions(cost_pct=0.001, slippage_pct=0.002, adjustment="qfq"),
    )

    assert result.exit_reason == "time_exit"
    assert result.gross_return_pct == 0.12
    assert result.return_pct == 0.1133
    assert result.cost_impact_pct == -0.0067
    assert result.options.adjustment == "qfq"


def test_backtest_requires_two_prices() -> None:
    with pytest.raises(ValueError, match="at least two price points"):
        SimpleBacktestEngine().run(build_report(), prices(100))


def test_backtest_requires_risk_controls() -> None:
    report = build_report()
    report = AnalysisReport(
        task_id=report.task_id,
        stock=report.stock,
        status=report.status,
        action=report.action,
        confidence=report.confidence,
        summary=report.summary,
        reasons=report.reasons,
        risks=report.risks,
        agent_views=report.agent_views,
        data_context=report.data_context,
    )

    with pytest.raises(ValueError, match="risk_controls"):
        SimpleBacktestEngine().run(report, prices(100, 101))
