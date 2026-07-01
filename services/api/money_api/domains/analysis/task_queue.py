"""In-memory analysis task queue for HTTP polling flows."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from threading import Lock, Thread
from typing import Callable
from uuid import uuid4

from money_api.domains.analysis.contracts import AnalysisStatus
from money_api.domains.analysis.service import AnalysisService


@dataclass(frozen=True)
class AnalysisTaskRecord:
    task_id: str
    symbol: str
    message: str
    status: str
    created_at: str
    updated_at: str
    report_id: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "symbol": self.symbol,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "report_id": self.report_id,
            "error": self.error,
        }


class InMemoryAnalysisTaskQueue:
    def __init__(self, service: AnalysisService, executor: Callable[[Callable[[], None]], None] | None = None):
        self.service = service
        self.executor = executor or self._default_executor
        self._records: dict[str, AnalysisTaskRecord] = {}
        self._lock = Lock()

    def create_analysis_task(self, symbol: str, message: str) -> AnalysisTaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        task_id = f"task-{uuid4().hex}"
        record = AnalysisTaskRecord(
            task_id=task_id,
            symbol=symbol,
            message=message,
            status=AnalysisStatus.QUEUED.value,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._records[task_id] = record
        self.executor(lambda: self._run_task(task_id))
        return record

    def get_task(self, task_id: str) -> AnalysisTaskRecord | None:
        with self._lock:
            return self._records.get(task_id)

    def _default_executor(self, operation: Callable[[], None]) -> None:
        Thread(target=operation, daemon=True).start()

    def _update(self, task_id: str, **changes: object) -> None:
        with self._lock:
            record = self._records[task_id]
            self._records[task_id] = replace(
                record,
                updated_at=datetime.now(timezone.utc).isoformat(),
                **changes,
            )

    def _run_task(self, task_id: str) -> None:
        record = self.get_task(task_id)
        if record is None:
            return
        next_status = (
            AnalysisStatus.DEEP_ANALYSIS.value
            if self.service.quick_router.needs_deep_analysis(record.message)
            else AnalysisStatus.QUICK_SCREENING.value
        )
        self._update(task_id, status=next_status)
        try:
            report = self.service.create_single_stock_analysis(record.symbol, record.message)
        except Exception as exc:
            self._update(task_id, status=AnalysisStatus.FAILED.value, error=str(exc))
            return
        self._update(task_id, status=AnalysisStatus.REPORT_READY.value, report_id=report.task_id)
