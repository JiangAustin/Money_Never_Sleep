from money_api.domains.analysis.contracts import AnalysisStatus
from money_api.domains.analysis.report_repository import InMemoryAnalysisReportRepository
from money_api.domains.analysis.task_queue import (
    AnalysisTaskRecord,
    InMemoryAnalysisTaskQueue,
    InMemoryAnalysisTaskRepository,
    JsonFileAnalysisTaskRepository,
)
from money_api.api.v1.router import build_default_analysis_service


def test_in_memory_task_repository_save_get_and_list() -> None:
    repository = InMemoryAnalysisTaskRepository()
    first = AnalysisTaskRecord(
        task_id="task-1",
        symbol="600519",
        message="first",
        status=AnalysisStatus.QUEUED.value,
        created_at="2026-07-01T00:00:00+00:00",
        updated_at="2026-07-01T00:00:00+00:00",
    )
    second = AnalysisTaskRecord(
        task_id="task-2",
        symbol="000001",
        message="second",
        status=AnalysisStatus.REPORT_READY.value,
        created_at="2026-07-01T00:00:01+00:00",
        updated_at="2026-07-01T00:00:01+00:00",
    )

    repository.save(first)
    repository.save(second)

    assert repository.get("task-1") == first
    assert [item.task_id for item in repository.list_recent(limit=1)] == ["task-2"]


def test_json_task_repository_saves_and_loads_records(tmp_path) -> None:
    repository = JsonFileAnalysisTaskRepository(tmp_path)
    record = AnalysisTaskRecord(
        task_id="task-1",
        symbol="600519",
        message="demo",
        status=AnalysisStatus.QUEUED.value,
        created_at="2026-07-01T00:00:00+00:00",
        updated_at="2026-07-01T00:00:00+00:00",
    )

    repository.save(record)

    assert repository.get("task-1") == record
    assert (tmp_path / "task-1.json").exists()


def test_json_task_repository_marks_inflight_tasks_failed_on_recover(tmp_path) -> None:
    repository = JsonFileAnalysisTaskRepository(tmp_path)
    repository.save(
        AnalysisTaskRecord(
            task_id="task-1",
            symbol="600519",
            message="demo",
            status=AnalysisStatus.DEEP_ANALYSIS.value,
            created_at="2026-07-01T00:00:00+00:00",
            updated_at="2026-07-01T00:00:00+00:00",
        )
    )

    recovered = repository.recover_incomplete("service restarted before task finished")

    assert recovered[0].status == AnalysisStatus.FAILED.value
    assert recovered[0].error == "service restarted before task finished"


def test_task_queue_uses_repository_and_recovers_incomplete_records(tmp_path) -> None:
    service = build_default_analysis_service(report_repository=InMemoryAnalysisReportRepository())
    repository = JsonFileAnalysisTaskRepository(tmp_path)
    repository.save(
        AnalysisTaskRecord(
            task_id="task-1",
            symbol="600519",
            message="demo",
            status=AnalysisStatus.QUEUED.value,
            created_at="2026-07-01T00:00:00+00:00",
            updated_at="2026-07-01T00:00:00+00:00",
        )
    )

    queue = InMemoryAnalysisTaskQueue(service=service, repository=repository, executor=lambda operation: operation())

    recovered = queue.get_task("task-1")

    assert recovered is not None
    assert recovered.status == AnalysisStatus.FAILED.value
    assert recovered.error == "service restarted before task finished"