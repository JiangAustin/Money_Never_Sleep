"""In-memory analysis task queue for HTTP polling flows."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock, Thread
from typing import Callable, Protocol
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

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "AnalysisTaskRecord":
        return cls(
            task_id=str(payload.get("task_id", "")),
            symbol=str(payload.get("symbol", "")),
            message=str(payload.get("message", "")),
            status=str(payload.get("status", "")),
            created_at=str(payload.get("created_at", "")),
            updated_at=str(payload.get("updated_at", "")),
            report_id=str(payload.get("report_id")) if payload.get("report_id") is not None else None,
            error=str(payload.get("error")) if payload.get("error") is not None else None,
        )


class AnalysisTaskRepository(Protocol):
    def save(self, record: AnalysisTaskRecord) -> AnalysisTaskRecord: ...
    def get(self, task_id: str) -> AnalysisTaskRecord | None: ...
    def list_recent(self, limit: int = 20) -> list[AnalysisTaskRecord]: ...
    def recover_incomplete(self, error_message: str) -> list[AnalysisTaskRecord]: ...


class InMemoryAnalysisTaskRepository:
    def __init__(self):
        self._records: dict[str, AnalysisTaskRecord] = {}

    def save(self, record: AnalysisTaskRecord) -> AnalysisTaskRecord:
        self._records[record.task_id] = record
        return record

    def get(self, task_id: str) -> AnalysisTaskRecord | None:
        return self._records.get(task_id)

    def list_recent(self, limit: int = 20) -> list[AnalysisTaskRecord]:
        records = sorted(self._records.values(), key=lambda item: item.updated_at, reverse=True)
        return records[:limit]

    def recover_incomplete(self, error_message: str) -> list[AnalysisTaskRecord]:
        recovered = []
        inflight = {
            AnalysisStatus.QUEUED.value,
            AnalysisStatus.COLLECTING_DATA.value,
            AnalysisStatus.QUICK_SCREENING.value,
            AnalysisStatus.DEEP_ANALYSIS.value,
            AnalysisStatus.RISK_REVIEW.value,
        }
        for task_id, record in list(self._records.items()):
            if record.status in inflight:
                updated = replace(
                    record,
                    status=AnalysisStatus.FAILED.value,
                    updated_at=datetime.now(timezone.utc).isoformat(),
                    error=error_message,
                )
                self._records[task_id] = updated
                recovered.append(updated)
        return recovered


def _safe_task_filename(task_id: str) -> str:
    if not task_id or "/" in task_id or "\\" in task_id or task_id in {".", ".."} or ".." in task_id:
        raise ValueError(f"unsafe task_id: {task_id}")
    return f"{task_id}.json"


class JsonFileAnalysisTaskRepository:
    def __init__(self, tasks_dir: str | Path):
        self.tasks_dir = Path(tasks_dir)

    def save(self, record: AnalysisTaskRecord) -> AnalysisTaskRecord:
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        path = self.tasks_dir / _safe_task_filename(record.task_id)
        path.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return record

    def get(self, task_id: str) -> AnalysisTaskRecord | None:
        try:
            path = self.tasks_dir / _safe_task_filename(task_id)
        except ValueError:
            return None
        if not path.exists():
            return None
        return AnalysisTaskRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list_recent(self, limit: int = 20) -> list[AnalysisTaskRecord]:
        if not self.tasks_dir.exists():
            return []
        records = []
        for path in self.tasks_dir.glob("*.json"):
            try:
                records.append(AnalysisTaskRecord.from_dict(json.loads(path.read_text(encoding="utf-8"))))
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                continue
        records.sort(key=lambda item: item.updated_at, reverse=True)
        return records[:limit]

    def recover_incomplete(self, error_message: str) -> list[AnalysisTaskRecord]:
        inflight = {
            AnalysisStatus.QUEUED.value,
            AnalysisStatus.COLLECTING_DATA.value,
            AnalysisStatus.QUICK_SCREENING.value,
            AnalysisStatus.DEEP_ANALYSIS.value,
            AnalysisStatus.RISK_REVIEW.value,
        }
        recovered = []
        for record in self.list_recent(limit=10_000):
            if record.status not in inflight:
                continue
            updated = replace(
                record,
                status=AnalysisStatus.FAILED.value,
                updated_at=datetime.now(timezone.utc).isoformat(),
                error=error_message,
            )
            self.save(updated)
            recovered.append(updated)
        return recovered


class InMemoryAnalysisTaskQueue:
    def __init__(
        self,
        service: AnalysisService,
        repository: AnalysisTaskRepository | None = None,
        executor: Callable[[Callable[[], None]], None] | None = None,
    ):
        self.service = service
        self.repository = repository or InMemoryAnalysisTaskRepository()
        self.executor = executor or self._default_executor
        self._records: dict[str, AnalysisTaskRecord] = {}
        self._lock = Lock()
        for record in self.repository.list_recent(limit=10_000):
            self._records[record.task_id] = record
        for record in self.repository.recover_incomplete("service restarted before task finished"):
            self._records[record.task_id] = record

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
        self.repository.save(record)
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
            updated = replace(
                record,
                updated_at=datetime.now(timezone.utc).isoformat(),
                **changes,
            )
            self._records[task_id] = updated
        self.repository.save(updated)

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
