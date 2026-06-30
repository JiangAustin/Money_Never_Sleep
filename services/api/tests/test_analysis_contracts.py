from money_api.domains.analysis.contracts import (
    AgentView,
    AnalysisReport,
    AnalysisStatus,
    ConfidenceLevel,
    DataContext,
    DecisionAction,
    RiskFinding,
    StockIdentity,
)


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

    assert payload["stock"] == {"code": "600519", "name": "贵州茅台", "market": "cn"}
    assert payload["status"] == "report_ready"
    assert payload["action"] == "watch"
    assert payload["confidence"] == "medium"
    assert payload["data_gaps"] == ["资金流不可用"]
    assert payload["risks"] == [{"level": "medium", "message": "短期偏离 MA5"}]