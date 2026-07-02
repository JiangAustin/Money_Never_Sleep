import json

from money_api.domains.analysis.contracts import (
    AnalysisReport,
    AnalysisStatus,
    ConfidenceLevel,
    DataContext,
    DecisionAction,
    StockIdentity,
)
from money_api.domains.analysis.report_repository import (
    AnalysisReportRecord,
    InMemoryAnalysisReportRepository,
    JsonFileAnalysisReportRepository,
)


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


def test_json_repository_saves_and_loads_report(tmp_path) -> None:
    repository = JsonFileAnalysisReportRepository(tmp_path)
    report = build_report("task-1")

    repository.save(report)

    assert repository.get("task-1") == report
    assert (tmp_path / "task-1.json").exists()


def test_json_repository_lists_recent_reports(tmp_path) -> None:
    repository = JsonFileAnalysisReportRepository(tmp_path)
    repository.save(build_report("task-1", "first"))
    repository.save(build_report("task-2", "second"))

    records = repository.list_recent(limit=2)

    assert {record.task_id for record in records} == {"task-1", "task-2"}
    assert records[0].created_at >= records[1].created_at


def test_json_repository_lists_legacy_reports_with_inner_provenance(tmp_path) -> None:
    repository = JsonFileAnalysisReportRepository(tmp_path)
    report = build_report("legacy-task").to_dict()
    report["data_sources"] = ["tencent", "eastmoney-news"]
    report["engine_source"] = "tradingagents"
    report["engine_mode"] = "auto"
    report["fallback_reason"] = "runner unavailable"
    (tmp_path / "legacy-task.json").write_text(
        """
{
  "task_id": "legacy-task",
  "created_at": "2026-07-02T00:00:00+00:00",
  "stock": {"code": "600519", "name": "贵州茅台", "market": "cn"},
  "status": "report_ready",
  "summary": "legacy summary",
  "report": %s
}
        """.strip()
        % json.dumps(report, ensure_ascii=False),
        encoding="utf-8",
    )

    records = repository.list_recent(limit=1)

    assert records[0].data_sources == ["tencent", "eastmoney-news"]
    assert records[0].engine_source == "tradingagents"
    assert records[0].engine_mode == "auto"
    assert records[0].fallback_reason == "runner unavailable"


def test_json_repository_skips_corrupt_files(tmp_path) -> None:
    repository = JsonFileAnalysisReportRepository(tmp_path)
    repository.save(build_report("task-1"))
    (tmp_path / "broken.json").write_text("not json", encoding="utf-8")

    records = repository.list_recent(limit=20)

    assert [record.task_id for record in records] == ["task-1"]


def test_json_repository_rejects_unsafe_task_id(tmp_path) -> None:
    repository = JsonFileAnalysisReportRepository(tmp_path)
    report = build_report("../escape")

    try:
        repository.save(report)
    except ValueError as exc:
        assert "unsafe task_id" in str(exc)
    else:
        raise AssertionError("expected unsafe task_id to be rejected")
