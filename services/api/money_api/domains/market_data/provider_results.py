"""Provider result contracts for market data collection."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProviderDiagnostic:
    kind: str
    source: str
    ok: bool
    error_type: str | None = None
    error_message: str | None = None
    fetched_at: str | None = None
    is_stale: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "source": self.source,
            "ok": self.ok,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "fetched_at": self.fetched_at,
            "is_stale": self.is_stale,
        }


@dataclass(frozen=True)
class ProviderResult:
    kind: str
    source: str
    ok: bool
    data: dict[str, Any] | list[dict[str, Any]] = field(default_factory=dict)
    error_type: str | None = None
    error_message: str | None = None
    fetched_at: str | None = None
    is_stale: bool = False

    @property
    def gap_name(self) -> str:
        return self.kind

    def to_diagnostic(self) -> dict[str, Any]:
        return ProviderDiagnostic(
            kind=self.kind,
            source=self.source,
            ok=self.ok,
            error_type=self.error_type,
            error_message=self.error_message,
            fetched_at=self.fetched_at,
            is_stale=self.is_stale,
        ).to_dict()
