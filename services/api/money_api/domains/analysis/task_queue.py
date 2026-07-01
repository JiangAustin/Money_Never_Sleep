"""In-memory analysis task queue for HTTP polling flows."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock, Thread
import time
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
    started_at: str | None = None
    timeout_s: int = 300
    retry_count: int = 0
    max_retries: int = 0
    next_retry_at: str | None = None
    next_retry_delay_s: int | None = None
    next_retry_policy: str | None = None
    report_id: str | None = None
    error: str | None = None
    retry_of: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "symbol": self.symbol,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "timeout_s": self.timeout_s,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "next_retry_at": self.next_retry_at,
            "next_retry_delay_s": self.next_retry_delay_s,
            "next_retry_policy": self.next_retry_policy,
            "report_id": self.report_id,
            "error": self.error,
            "retry_of": self.retry_of,
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
            started_at=str(payload.get("started_at")) if payload.get("started_at") is not None else None,
            timeout_s=int(payload.get("timeout_s", 300)),
            retry_count=int(payload.get("retry_count", 0)),
            max_retries=int(payload.get("max_retries", 0)),
            next_retry_at=str(payload.get("next_retry_at")) if payload.get("next_retry_at") is not None else None,
            next_retry_delay_s=int(payload.get("next_retry_delay_s")) if payload.get("next_retry_delay_s") is not None else None,
            next_retry_policy=str(payload.get("next_retry_policy")) if payload.get("next_retry_policy") is not None else None,
            report_id=str(payload.get("report_id")) if payload.get("report_id") is not None else None,
            error=str(payload.get("error")) if payload.get("error") is not None else None,
            retry_of=str(payload.get("retry_of")) if payload.get("retry_of") is not None else None,
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
        default_timeout_s: int = 300,
        retry_backoff_base_s: int = 2,
        retry_backoff_max_s: int = 30,
        retry_backoff_factor: int = 2,
        retry_jitter_ratio: float = 0.0,
        retry_timeout_multiplier: int = 1,
    ):
        self.service = service
        self.repository = repository or InMemoryAnalysisTaskRepository()
        self.executor = executor or self._default_executor
        self.default_timeout_s = default_timeout_s
        self.retry_backoff_base_s = retry_backoff_base_s
        self.retry_backoff_max_s = retry_backoff_max_s
        self.retry_backoff_factor = retry_backoff_factor
        self.retry_jitter_ratio = retry_jitter_ratio
        self.retry_timeout_multiplier = retry_timeout_multiplier
        self._retry_random: Callable[[], float] = random.random
        self._records: dict[str, AnalysisTaskRecord] = {}
        self._lock = Lock()
        for record in self.repository.list_recent(limit=10_000):
            self._records[record.task_id] = record
        for record in self.repository.recover_incomplete("service restarted before task finished"):
            self._records[record.task_id] = record

    def create_analysis_task(
        self,
        symbol: str,
        message: str,
        timeout_s: int | None = None,
        max_retries: int | None = None,
    ) -> AnalysisTaskRecord:
        return self._create_task_record(symbol=symbol, message=message, timeout_s=timeout_s, max_retries=max_retries)

    def cancel_task(self, task_id: str) -> AnalysisTaskRecord | None:
        task = self.get_task(task_id)
        if task is None:
            return None
        if task.status in {AnalysisStatus.REPORT_READY.value, AnalysisStatus.FAILED.value, AnalysisStatus.CANCELLED.value}:
            return task
        self._update(task_id, status=AnalysisStatus.CANCELLED.value, error="cancelled by user")
        return self.get_task(task_id)

    def retry_task(self, task_id: str) -> AnalysisTaskRecord | None:
        task = self.get_task(task_id)
        if task is None:
            return None
        if task.status not in {AnalysisStatus.FAILED.value, AnalysisStatus.CANCELLED.value}:
            return None
        return self._create_task_record(
            symbol=task.symbol,
            message=task.message,
            retry_of=task.task_id,
            timeout_s=task.timeout_s,
            retry_count=task.retry_count + 1,
            max_retries=task.max_retries,
        )

    def _create_task_record(
        self,
        symbol: str,
        message: str,
        retry_of: str | None = None,
        timeout_s: int | None = None,
        retry_count: int = 0,
        max_retries: int | None = None,
    ) -> AnalysisTaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        task_id = f"task-{uuid4().hex}"
        record = AnalysisTaskRecord(
            task_id=task_id,
            symbol=symbol,
            message=message,
            status=AnalysisStatus.QUEUED.value,
            created_at=now,
            updated_at=now,
            started_at=now,
            timeout_s=int(timeout_s or self.default_timeout_s),
            retry_count=retry_count,
            max_retries=int(max_retries or 0),
            retry_of=retry_of,
        )
        with self._lock:
            self._records[task_id] = record
        self.repository.save(record)
        self.executor(lambda: self._run_task(task_id))
        return record

    def get_task(self, task_id: str) -> AnalysisTaskRecord | None:
        self._expire_task_if_needed(task_id)
        self._maybe_retry(task_id)
        with self._lock:
            return self._records.get(task_id)

    def list_tasks(self, limit: int = 20) -> list[AnalysisTaskRecord]:
        for task_id in list(self._records.keys()):
            self._expire_task_if_needed(task_id)
            self._maybe_retry(task_id)
        with self._lock:
            records = sorted(self._records.values(), key=lambda item: item.updated_at, reverse=True)
        return records[:limit]

    def _default_executor(self, operation: Callable[[], None]) -> None:
        Thread(target=operation, daemon=True).start()

    def start_watchdog(self, interval_s: float = 1.0, iterations: int | None = None) -> Thread:
        def watch() -> None:
            run_count = 0
            while iterations is None or run_count < iterations:
                self.list_tasks(limit=10_000)
                run_count += 1
                if iterations is not None and run_count >= iterations:
                    break
                time.sleep(interval_s)

        thread = Thread(target=watch, daemon=True)
        thread.start()
        return thread

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _expire_task_if_needed(self, task_id: str) -> None:
        with self._lock:
            record = self._records.get(task_id)
        if record is None:
            return
        if record.status not in {
            AnalysisStatus.QUEUED.value,
            AnalysisStatus.COLLECTING_DATA.value,
            AnalysisStatus.QUICK_SCREENING.value,
            AnalysisStatus.DEEP_ANALYSIS.value,
            AnalysisStatus.RISK_REVIEW.value,
        }:
            return
        if not record.started_at:
            return
        started_at = datetime.fromisoformat(record.started_at)
        current = datetime.fromisoformat(self._now())
        if (current - started_at).total_seconds() < record.timeout_s:
            return
        self._update(task_id, status=AnalysisStatus.FAILED.value, error=f"task timed out after {record.timeout_s}s")
        self._maybe_retry(task_id)

    def _update(self, task_id: str, **changes: object) -> None:
        with self._lock:
            record = self._records[task_id]
            updated = replace(
                record,
                updated_at=self._now(),
                **changes,
            )
            self._records[task_id] = updated
        self.repository.save(updated)

    def _maybe_retry(self, task_id: str) -> None:
        with self._lock:
            task = self._records.get(task_id)
        if task is None:
            return
        if task.status != AnalysisStatus.FAILED.value:
            return
        if task.retry_count >= task.max_retries:
            return
        if self._has_retry_child(task.task_id):
            return
        if task.next_retry_at is None:
            delay_s, policy = self._compute_retry_delay_s(task.retry_count, task.error)
            self._update(
                task_id,
                next_retry_at=(datetime.fromisoformat(self._now()) + timedelta(seconds=delay_s)).isoformat(),
                next_retry_delay_s=delay_s,
                next_retry_policy=policy,
            )
            return
        if datetime.fromisoformat(self._now()) < datetime.fromisoformat(task.next_retry_at):
            return
        self._create_task_record(
            symbol=task.symbol,
            message=task.message,
            retry_of=task.task_id,
            timeout_s=task.timeout_s,
            retry_count=task.retry_count + 1,
            max_retries=task.max_retries,
        )

    def _has_retry_child(self, task_id: str) -> bool:
        with self._lock:
            return any(record.retry_of == task_id for record in self._records.values())

    def _compute_retry_delay_s(self, retry_count: int, error: str | None = None) -> tuple[int, str]:
        delay = self.retry_backoff_base_s * (self.retry_backoff_factor ** retry_count)
        normalized_error = (error or "").lower()
        policy = "generic"
        if "timeout" in normalized_error or "timed out" in normalized_error:
            delay *= self.retry_timeout_multiplier
            policy = "timeout"
        delay = min(self.retry_backoff_max_s, delay)
        if self.retry_jitter_ratio > 0:
            jitter = int(delay * self.retry_jitter_ratio * self._retry_random())
            delay = min(self.retry_backoff_max_s, delay + jitter)
        return max(1, delay), policy

    def _run_task(self, task_id: str) -> None:
        record = self.get_task(task_id)
        if record is None:
            return
        if record.status == AnalysisStatus.CANCELLED.value:
            return
        next_status = (
            AnalysisStatus.DEEP_ANALYSIS.value
            if self.service.quick_router.needs_deep_analysis(record.message)
            else AnalysisStatus.QUICK_SCREENING.value
        )
        self._update(task_id, status=next_status, started_at=record.started_at or self._now())
        if (current := self.get_task(task_id)) is not None and current.status == AnalysisStatus.CANCELLED.value:
            return
        try:
            report = self.service.create_single_stock_analysis(record.symbol, record.message)
        except Exception as exc:
            if (current := self.get_task(task_id)) is not None and current.status == AnalysisStatus.CANCELLED.value:
                return
            self._update(task_id, status=AnalysisStatus.FAILED.value, error=str(exc))
            self._maybe_retry(task_id)
            return
        if (current := self.get_task(task_id)) is not None and current.status == AnalysisStatus.CANCELLED.value:
            return
        self._update(task_id, status=AnalysisStatus.REPORT_READY.value, report_id=report.task_id)
