"""Report repository contracts and implementations."""

from dataclasses import dataclass
from datetime import datetime, timezone
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
