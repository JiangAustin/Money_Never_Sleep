from money_api.domains.analysis.contracts import (
    AnalysisReport,
    AnalysisStatus,
    ConfidenceLevel,
    DataContext,
    DecisionAction,
    StockIdentity,
)
from money_api.domains.analysis.report_repository import AnalysisReportRecord, InMemoryAnalysisReportRepository


def build_report(task_id: str, summary: str = "summary") -> AnalysisReport:
    stock = StockIdentity(code="600519", name="贵州茅台")
    return AnalysisReport(
        task_id=task_id,
        stock=stock,
        status=AnalysisStatus.REPORT_READY,
        action=DecisionAction.WATCH,
        confidence=ConfidenceLevel.MEDIUM,
        summary=summary,
        reasons=[],
        risks=[],
        agent_views=[],
        data_context=DataContext(stock=stock),
    )


def test_in_memory_repository_saves_and_gets_report() -> None:
    repository = InMemoryAnalysisReportRepository()
    report = build_report("task-1")

    record = repository.save(report)

    assert isinstance(record, AnalysisReportRecord)
    assert record.task_id == "task-1"
    assert repository.get("task-1") == report


def test_in_memory_repository_lists_recent_reports() -> None:
    repository = InMemoryAnalysisReportRepository()
    repository.save(build_report("task-1", "first"))
    repository.save(build_report("task-2", "second"))

    records = repository.list_recent(limit=1)

    assert [record.task_id for record in records] == ["task-2"]
    assert records[0].summary == "second"
