from money_api.domains.analysis.contracts import AnalysisReport, AnalysisStatus, ConfidenceLevel, DataContext, DecisionAction, StockIdentity
from money_api.domains.market_data.provider_results import ProviderDiagnostic, ProviderResult


def test_provider_result_success_to_diagnostic() -> None:
    result = ProviderResult(kind="quote", source="static", ok=True, data={"price": 1688.0})

    assert result.to_diagnostic() == {
        "kind": "quote",
        "source": "static",
        "ok": True,
        "error_type": None,
        "error_message": None,
        "fetched_at": None,
        "is_stale": False,
    }


def test_provider_result_failure_to_gap_reason() -> None:
    result = ProviderResult(kind="quote", source="tencent", ok=False, data={}, error_type="TimeoutError", error_message="timeout")

    assert result.gap_name == "quote"
    assert result.to_diagnostic()["error_message"] == "timeout"


def test_analysis_report_exposes_data_diagnostics() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    diagnostic = ProviderDiagnostic(kind="quote", source="tencent", ok=False, error_type="TimeoutError", error_message="timeout")
    context = DataContext(stock=stock, gaps=["quote"], diagnostics=[diagnostic.to_dict()])
    report = AnalysisReport(
        task_id="task-1",
        stock=stock,
        status=AnalysisStatus.REPORT_READY,
        action=DecisionAction.WATCH,
        confidence=ConfidenceLevel.LOW,
        summary="partial",
        reasons=[],
        risks=[],
        agent_views=[],
        data_context=context,
    )

    assert report.to_dict()["data_diagnostics"] == [diagnostic.to_dict()]
