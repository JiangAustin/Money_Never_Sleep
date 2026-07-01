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


def test_task_queue_can_cancel_queued_task() -> None:
    service = build_default_analysis_service(report_repository=InMemoryAnalysisReportRepository())
    repository = InMemoryAnalysisTaskRepository()
    scheduled = []
    queue = InMemoryAnalysisTaskQueue(service=service, repository=repository, executor=lambda operation: scheduled.append(operation))

    task = queue.create_analysis_task("贵州茅台", "请全面分析")
    cancelled = queue.cancel_task(task.task_id)

    assert cancelled is not None
    assert cancelled.status == "cancelled"
    assert cancelled.error == "cancelled by user"


def test_task_queue_can_retry_failed_task() -> None:
    service = build_default_analysis_service(report_repository=InMemoryAnalysisReportRepository())
    repository = InMemoryAnalysisTaskRepository()
    queue = InMemoryAnalysisTaskQueue(service=service, repository=repository, executor=lambda operation: operation())
    failed = AnalysisTaskRecord(
        task_id="task-failed",
        symbol="600519",
        message="请全面分析",
        status=AnalysisStatus.FAILED.value,
        created_at="2026-07-01T00:00:00+00:00",
        updated_at="2026-07-01T00:00:00+00:00",
        error="boom",
    )
    repository.save(failed)
    queue._records[failed.task_id] = failed

    retried = queue.retry_task(failed.task_id)

    assert retried is not None
    assert retried.task_id != failed.task_id
    assert retried.status in {AnalysisStatus.QUEUED.value, AnalysisStatus.QUICK_SCREENING.value, AnalysisStatus.DEEP_ANALYSIS.value, AnalysisStatus.REPORT_READY.value}
    assert retried.message == failed.message


def test_task_queue_marks_timed_out_task_failed() -> None:
    service = build_default_analysis_service(report_repository=InMemoryAnalysisReportRepository())
    repository = InMemoryAnalysisTaskRepository()
    queue = InMemoryAnalysisTaskQueue(service=service, repository=repository, executor=lambda operation: None)
    expired = AnalysisTaskRecord(
        task_id="task-timeout",
        symbol="600519",
        message="请全面分析",
        status=AnalysisStatus.DEEP_ANALYSIS.value,
        created_at="2026-07-01T00:00:00+00:00",
        updated_at="2026-07-01T00:00:00+00:00",
        started_at="2026-07-01T00:00:00+00:00",
        timeout_s=1,
    )
    repository.save(expired)
    queue._records[expired.task_id] = expired
    queue._now = lambda: "2026-07-01T00:00:05+00:00"  # type: ignore[attr-defined]

    task = queue.get_task("task-timeout")

    assert task is not None
    assert task.status == AnalysisStatus.FAILED.value
    assert task.error == "task timed out after 1s"


def test_task_queue_auto_retries_timed_out_task() -> None:
    service = build_default_analysis_service(report_repository=InMemoryAnalysisReportRepository())
    repository = InMemoryAnalysisTaskRepository()
    queue = InMemoryAnalysisTaskQueue(service=service, repository=repository, executor=lambda operation: None)
    expired = AnalysisTaskRecord(
        task_id="task-timeout",
        symbol="600519",
        message="请全面分析",
        status=AnalysisStatus.DEEP_ANALYSIS.value,
        created_at="2026-07-01T00:00:00+00:00",
        updated_at="2026-07-01T00:00:00+00:00",
        started_at="2026-07-01T00:00:00+00:00",
        timeout_s=1,
        max_retries=1,
        retry_count=0,
    )
    repository.save(expired)
    queue._records[expired.task_id] = expired
    queue._now = lambda: "2026-07-01T00:00:05+00:00"  # type: ignore[attr-defined]

    task = queue.get_task("task-timeout")
    retries = [record for record in queue.list_tasks(limit=20) if record.retry_of == "task-timeout"]

    assert task is not None
    assert task.status == AnalysisStatus.FAILED.value
    assert task.error == "task timed out after 1s"
    assert task.next_retry_at == "2026-07-01T00:00:07+00:00"
    assert len(retries) == 0


def test_task_queue_watchdog_dispatches_scheduled_retry_when_due() -> None:
    service = build_default_analysis_service(report_repository=InMemoryAnalysisReportRepository())
    repository = InMemoryAnalysisTaskRepository()
    queue = InMemoryAnalysisTaskQueue(service=service, repository=repository, executor=lambda operation: None)
    expired = AnalysisTaskRecord(
        task_id="task-timeout",
        symbol="600519",
        message="请全面分析",
        status=AnalysisStatus.DEEP_ANALYSIS.value,
        created_at="2026-07-01T00:00:00+00:00",
        updated_at="2026-07-01T00:00:00+00:00",
        started_at="2026-07-01T00:00:00+00:00",
        timeout_s=1,
        max_retries=1,
        retry_count=0,
    )
    repository.save(expired)
    queue._records[expired.task_id] = expired

    queue._now = lambda: "2026-07-01T00:00:05+00:00"  # type: ignore[attr-defined]
    task = queue.get_task("task-timeout")
    assert task is not None
    assert task.next_retry_at == "2026-07-01T00:00:07+00:00"

    queue._now = lambda: "2026-07-01T00:00:06+00:00"  # type: ignore[attr-defined]
    watchdog = queue.start_watchdog(interval_s=0.01, iterations=1)
    watchdog.join(timeout=1)
    before_due_retries = [record for record in queue.list_tasks(limit=20) if record.retry_of == "task-timeout"]
    assert len(before_due_retries) == 0

    queue._now = lambda: "2026-07-01T00:00:08+00:00"  # type: ignore[attr-defined]
    watchdog = queue.start_watchdog(interval_s=0.01, iterations=1)
    watchdog.join(timeout=1)
    due_retries = [record for record in queue.list_tasks(limit=20) if record.retry_of == "task-timeout"]
    assert len(due_retries) == 1
    assert due_retries[0].retry_count == 1


def test_task_queue_start_watchdog_sweeps_timeouts() -> None:
    service = build_default_analysis_service(report_repository=InMemoryAnalysisReportRepository())
    repository = InMemoryAnalysisTaskRepository()
    queue = InMemoryAnalysisTaskQueue(service=service, repository=repository, executor=lambda operation: None)
    expired = AnalysisTaskRecord(
        task_id="task-timeout",
        symbol="600519",
        message="请全面分析",
        status=AnalysisStatus.DEEP_ANALYSIS.value,
        created_at="2026-07-01T00:00:00+00:00",
        updated_at="2026-07-01T00:00:00+00:00",
        started_at="2026-07-01T00:00:00+00:00",
        timeout_s=1,
    )
    repository.save(expired)
    queue._records[expired.task_id] = expired
    queue._now = lambda: "2026-07-01T00:00:05+00:00"  # type: ignore[attr-defined]

    watchdog = queue.start_watchdog(interval_s=0.01, iterations=1)
    watchdog.join(timeout=1)

    task = queue.get_task("task-timeout")

    assert task is not None
    assert task.status == AnalysisStatus.FAILED.value