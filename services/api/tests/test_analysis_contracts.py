from dataclasses import FrozenInstanceError

import pytest

from money_api.domains.analysis.contracts import (
    AgentView,
    AnalysisReport,
    AnalysisStatus,
    BacktestOptions,
    BacktestPricePoint,
    BacktestResult,
    ConfidenceLevel,
    DataContext,
    DataTrustScore,
    DecisionAction,
    EngineTelemetry,
    EngineCostGuardrail,
    InvestmentPlan,
    MarketEvent,
    MarketEventType,
    PortfolioPositionBudget,
    PortfolioRiskBudget,
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


def test_market_event_round_trip() -> None:
    event = MarketEvent(
        event_type=MarketEventType.EARNINGS_FORECAST,
        title="示例公司发布2026年半年度业绩预告",
        source="static",
        summary="识别为业绩预告类事件，属于高优先级基本面信号。",
        confidence="high",
        priority="high",
        evidence_scope="title+content",
        evidence_excerpt="公告正文说明业绩预告并预计同比增长",
        time="2026-07-01",
        content="预计同比增长",
        url="https://example.com/event",
        matched_keywords=["业绩预告"],
    )

    assert MarketEvent.from_dict(event.to_dict()) == event


def test_market_event_from_dict_tolerates_unknown_event_type() -> None:
    event = MarketEvent.from_dict(
        {
            "event_type": "future_event_type",
            "title": "未知事件公告",
            "source": "fixture",
            "summary": "未知事件类型应安全降级。",
        }
    )

    assert event.event_type == MarketEventType.OTHER


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
    assert context.events == []
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
        events=[
            MarketEvent(
                event_type=MarketEventType.GUARANTEE,
                title="示例公司对外担保进展公告",
                source="sina-bulletin",
                summary="识别为担保类事件，属于高优先级风险事件。",
                confidence="high",
                priority="high",
                evidence_scope="title",
                evidence_excerpt="示例公司对外担保进展公告",
            )
        ],
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
    assert payload["data_context"]["events"][0]["event_type"] == "guarantee"
    assert payload["data_context"]["events"][0]["evidence_excerpt"] == "示例公司对外担保进展公告"
    assert payload["data_sources"] == []
    assert payload["engine_source"] == "mock"
    assert payload["engine_mode"] == "mock"
    assert payload["investment_plan"] is None
    assert payload["data_trust"] is None
    assert payload["engine_telemetry"] is None
    assert payload["engine_cost_guardrail"] is None


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
        data_sources=["tencent"],
        engine_source="tradingagents",
        engine_mode="auto",
        fallback_reason="mock fallback",
    )

    payload = report.to_dict()
    restored = AnalysisReport.from_dict(payload)

    assert payload["data_context"]["quote"]["price"] == 1688.0
    assert payload["data_sources"] == ["tencent"]
    assert payload["engine_source"] == "tradingagents"
    assert payload["engine_mode"] == "auto"
    assert payload["fallback_reason"] == "mock fallback"
    assert restored == report


def test_investment_plan_round_trip() -> None:
    plan = InvestmentPlan(
        direction=DecisionAction.BUY,
        target_position_pct=0.05,
        entry_conditions=["价格站上 20 日线"],
        exit_conditions=["跌破止损线", "事件逻辑失效"],
        stop_loss_pct=0.08,
        take_profit_pct=0.15,
        observation_window="5-20 个交易日",
        review_conditions=["每个交易日收盘后复核"],
        rationale=["基本面事件改善", "风险约束可控"],
        risk_notes=["流动性不足时降低仓位"],
    )

    assert InvestmentPlan.from_dict(plan.to_dict()) == plan


def test_data_trust_score_round_trip() -> None:
    trust = DataTrustScore(
        score=78,
        level="medium",
        summary="数据可信度中等，存在少量缺口。",
        signals=["quote 真实", "news 真实"],
        penalties=["存在 1 个数据缺口"],
        data_sources=["tencent", "eastmoney"],
        data_gaps=["fund_flow"],
        diagnostics_ok=3,
        diagnostics_failed=1,
        engine_source="tradingagents",
        engine_mode="auto",
        fallback_reason=None,
    )

    assert DataTrustScore.from_dict(trust.to_dict()) == trust


def test_engine_telemetry_round_trip() -> None:
    telemetry = EngineTelemetry(
        runtime_ms=128,
        execution_path="fallback",
        cost_tier="high",
        estimated_request_count=2,
        engine_source="mock",
        engine_mode="auto",
        failure_type="RuntimeError",
        failure_reason="boom",
        notes=["primary engine failed", "fallback to mock"],
    )

    assert EngineTelemetry.from_dict(telemetry.to_dict()) == telemetry


def test_engine_cost_guardrail_round_trip() -> None:
    guardrail = EngineCostGuardrail(
        status="over_budget",
        summary="引擎运行超出预算阈值，建议降级或复核。",
        alerts=["cost_tier:high", "runtime_ms:4820"],
        max_runtime_ms=3000,
        max_request_count=1,
        max_cost_tier="medium",
        runtime_ms=4820,
        estimated_request_count=2,
        cost_tier="high",
        engine_source="tradingagents",
        engine_mode="tradingagents",
    )

    assert EngineCostGuardrail.from_dict(guardrail.to_dict()) == guardrail


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


def test_backtest_result_round_trip() -> None:
    options = BacktestOptions(cost_pct=0.001, slippage_pct=0.002, adjustment="qfq")
    result = BacktestResult(
        task_id="task-1",
        entry_date="2026-07-01",
        exit_date="2026-07-05",
        entry_price=100.0,
        exit_price=112.0,
        return_pct=0.12,
        gross_return_pct=0.12,
        cost_impact_pct=0,
        max_drawdown_pct=-0.03,
        holding_days=4,
        exit_reason="take_profit",
        price_path=[BacktestPricePoint(date="2026-07-01", close=100.0)],
        options=options,
    )

    assert BacktestResult.from_dict(result.to_dict()) == result


def test_backtest_options_round_trip() -> None:
    options = BacktestOptions(cost_pct=0.001, slippage_pct=0.002, adjustment="qfq")

    assert BacktestOptions.from_dict(options.to_dict()) == options


def test_portfolio_risk_budget_round_trip() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    rule = RiskControlRule(name="confidence", level="medium", message="中等置信度")
    budget = PortfolioRiskBudget(
        total_position_pct=0.1,
        cash_reserve_pct=0.9,
        max_total_position_pct=0.6,
        max_single_position_pct=0.2,
        positions=[
            PortfolioPositionBudget(
                task_id="task-1",
                stock=stock,
                action=DecisionAction.WATCH,
                confidence=ConfidenceLevel.MEDIUM,
                budget_position_pct=0.1,
                source_position_pct=0.1,
                rules=[rule],
            )
        ],
        rules=[rule],
        disclaimer="非投资建议",
    )

    assert PortfolioRiskBudget.from_dict(budget.to_dict()) == budget
