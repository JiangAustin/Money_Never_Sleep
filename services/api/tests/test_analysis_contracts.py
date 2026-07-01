from dataclasses import FrozenInstanceError

import pytest

from money_api.domains.analysis.contracts import (
    AgentView,
    AnalysisReport,
    AnalysisStatus,
    ConfidenceLevel,
    DataContext,
    DecisionAction,
    RiskControlPlan,
    RiskControlRule,
    RiskFinding,
    StockIdentity,
)


def test_stock_identity_to_dict() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台", market="cn")

    assert stock.to_dict() == {"code": "600519", "name": "贵州茅台", "market": "cn"}


def test_risk_finding_to_dict() -> None:
    risk = RiskFinding(level="medium", message="短期偏离 MA5")

    assert risk.to_dict() == {"level": "medium", "message": "短期偏离 MA5"}


def test_agent_view_to_dict() -> None:
    view = AgentView(agent="Market Analyst", conclusion="趋势偏强")

    assert view.to_dict() == {"agent": "Market Analyst", "conclusion": "趋势偏强"}


def test_analysis_contract_enum_values() -> None:
    assert AnalysisStatus.REPORT_READY.value == "report_ready"
    assert DecisionAction.WATCH.value == "watch"
    assert ConfidenceLevel.MEDIUM.value == "medium"


def test_data_context_defaults_are_empty_collections() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")

    context = DataContext(stock=stock)

    assert context.quote == {}
    assert context.technicals == {}
    assert context.fundamentals == {}
    assert context.news == []
    assert context.gaps == []


def test_frozen_dataclasses_reject_mutation() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台", market="cn")

    with pytest.raises(FrozenInstanceError):
        stock.code = "000001"  # type: ignore[misc]


def test_report_to_dict_contains_required_sections() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台", market="cn")
    context = DataContext(
        stock=stock,
        quote={"price": 1688.0},
        technicals={"ma5": 1660.0},
        fundamentals={"pe_ttm": 28.5},
        news=[{"title": "业绩稳定"}],
        gaps=["资金流不可用"],
    )
    report = AnalysisReport(
        task_id="task-1",
        stock=stock,
        status=AnalysisStatus.REPORT_READY,
        action=DecisionAction.WATCH,
        confidence=ConfidenceLevel.MEDIUM,
        summary="等待回踩确认",
        reasons=["趋势仍在"],
        risks=[RiskFinding(level="medium", message="短期偏离 MA5")],
        agent_views=[AgentView(agent="Market Analyst", conclusion="趋势偏强")],
        data_context=context,
    )

    payload = report.to_dict()

    assert payload["task_id"] == "task-1"
    assert payload["stock"] == {"code": "600519", "name": "贵州茅台", "market": "cn"}
    assert payload["status"] == "report_ready"
    assert payload["action"] == "watch"
    assert payload["confidence"] == "medium"
    assert payload["summary"] == "等待回踩确认"
    assert payload["reasons"] == ["趋势仍在"]
    assert payload["agent_views"] == [{"agent": "Market Analyst", "conclusion": "趋势偏强"}]
    assert payload["data_gaps"] == ["资金流不可用"]
    assert payload["risks"] == [{"level": "medium", "message": "短期偏离 MA5"}]


def test_data_context_round_trip_preserves_payloads() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    context = DataContext(
        stock=stock,
        quote={"price": 1688.0},
        technicals={"ma5": 1660.0},
        fundamentals={"pe_ttm": 28.5},
        news=[{"title": "业绩稳定"}],
        gaps=["news"],
        diagnostics=[{"kind": "quote", "source": "tencent", "ok": True}],
    )

    restored = DataContext.from_dict(context.to_dict())

    assert restored == context


def test_analysis_report_round_trip_preserves_data_context() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    context = DataContext(stock=stock, quote={"price": 1688.0}, diagnostics=[{"kind": "quote", "ok": True}])
    report = AnalysisReport(
        task_id="task-1",
        stock=stock,
        status=AnalysisStatus.REPORT_READY,
        action=DecisionAction.WATCH,
        confidence=ConfidenceLevel.MEDIUM,
        summary="summary",
        reasons=["reason"],
        risks=[RiskFinding(level="low", message="risk")],
        agent_views=[AgentView(agent="agent", conclusion="view")],
        data_context=context,
    )

    payload = report.to_dict()
    restored = AnalysisReport.from_dict(payload)

    assert payload["data_context"]["quote"]["price"] == 1688.0
    assert restored == report


def test_risk_control_plan_round_trip() -> None:
    plan = RiskControlPlan(
        max_position_pct=0.1,
        stop_loss_pct=0.08,
        take_profit_pct=0.15,
        time_horizon="5-20 个交易日",
        rules=[RiskControlRule(name="confidence", level="medium", message="中等置信度")],
        disclaimer="非投资建议",
    )

    assert RiskControlPlan.from_dict(plan.to_dict()) == plan