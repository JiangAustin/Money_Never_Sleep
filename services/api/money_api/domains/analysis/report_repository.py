"""Report repository contracts and implementations."""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from money_api.domains.analysis.contracts import AnalysisReport


@dataclass(frozen=True)
class AnalysisReportRecord:
    task_id: str
    created_at: str
    stock: dict[str, str]
    status: str
    summary: str
    report: dict[str, object]

    @classmethod
    def from_report(cls, report: AnalysisReport, created_at: str | None = None) -> "AnalysisReportRecord":
        timestamp = created_at or datetime.now(timezone.utc).isoformat()
        payload = report.to_dict()
        return cls(
            task_id=report.task_id,
            created_at=timestamp,
            stock=report.stock.to_dict(),
            status=report.status.value,
            summary=report.summary,
            report=payload,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "created_at": self.created_at,
            "stock": dict(self.stock),
            "status": self.status,
            "summary": self.summary,
            "report": dict(self.report),
        }


class AnalysisReportRepository(Protocol):
    def save(self, report: AnalysisReport) -> AnalysisReportRecord: ...
    def get(self, task_id: str) -> AnalysisReport | None: ...
    def list_recent(self, limit: int = 20) -> list[AnalysisReportRecord]: ...


class InMemoryAnalysisReportRepository:
    def __init__(self):
        self._records: dict[str, AnalysisReportRecord] = {}

    def save(self, report: AnalysisReport) -> AnalysisReportRecord:
        record = AnalysisReportRecord.from_report(report)
        self._records[report.task_id] = record
        return record

    def get(self, task_id: str) -> AnalysisReport | None:
        record = self._records.get(task_id)
        return AnalysisReport.from_dict(record.report) if record is not None else None

    def list_recent(self, limit: int = 20) -> list[AnalysisReportRecord]:
        records = sorted(self._records.values(), key=lambda record: record.created_at, reverse=True)
        return records[:limit]


def _safe_report_filename(task_id: str) -> str:
    if not task_id or "/" in task_id or "\\" in task_id or task_id in {".", ".."} or ".." in task_id:
        raise ValueError(f"unsafe task_id: {task_id}")
    return f"{task_id}.json"


class JsonFileAnalysisReportRepository:
    def __init__(self, reports_dir: str | Path):
        self.reports_dir = Path(reports_dir)

    def save(self, report: AnalysisReport) -> AnalysisReportRecord:
        record = AnalysisReportRecord.from_report(report)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        path = self.reports_dir / _safe_report_filename(report.task_id)
        path.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return record

    def get(self, task_id: str) -> AnalysisReport | None:
        try:
            path = self.reports_dir / _safe_report_filename(task_id)
        except ValueError:
            return None
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return AnalysisReport.from_dict(payload["report"])

    def list_recent(self, limit: int = 20) -> list[AnalysisReportRecord]:
        if not self.reports_dir.exists():
            return []
        records = []
        for path in self.reports_dir.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                records.append(
                    AnalysisReportRecord(
                        task_id=str(payload["task_id"]),
                        created_at=str(payload["created_at"]),
                        stock=dict(payload.get("stock", {})),
                        status=str(payload.get("status", "")),
                        summary=str(payload.get("summary", "")),
                        report=dict(payload.get("report", {})),
                    )
                )
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                continue
        records.sort(key=lambda record: record.created_at, reverse=True)
        return records[:limit]
