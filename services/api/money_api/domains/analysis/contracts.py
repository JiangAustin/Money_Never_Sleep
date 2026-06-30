"""Analysis domain contracts for Money_Never_sleep."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AnalysisStatus(str, Enum):
    QUEUED = "queued"
    COLLECTING_DATA = "collecting_data"
    QUICK_SCREENING = "quick_screening"
    DEEP_ANALYSIS = "deep_analysis"
    RISK_REVIEW = "risk_review"
    REPORT_READY = "report_ready"
    FAILED = "failed"


class DecisionAction(str, Enum):
    BUY = "buy"
    WATCH = "watch"
    SELL = "sell"
    WAIT = "wait"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class StockIdentity:
    code: str
    name: str
    market: str = "cn"

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "name": self.name, "market": self.market}


@dataclass(frozen=True)
class RiskFinding:
    level: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"level": self.level, "message": self.message}


@dataclass(frozen=True)
class AgentView:
    agent: str
    conclusion: str

    def to_dict(self) -> dict[str, str]:
        return {"agent": self.agent, "conclusion": self.conclusion}


@dataclass(frozen=True)
class DataContext:
    stock: StockIdentity
    quote: dict[str, Any] = field(default_factory=dict)
    technicals: dict[str, Any] = field(default_factory=dict)
    fundamentals: dict[str, Any] = field(default_factory=dict)
    news: list[dict[str, Any]] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AnalysisReport:
    task_id: str
    stock: StockIdentity
    status: AnalysisStatus
    action: DecisionAction
    confidence: ConfidenceLevel
    summary: str
    reasons: list[str]
    risks: list[RiskFinding]
    agent_views: list[AgentView]
    data_context: DataContext

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "stock": self.stock.to_dict(),
            "status": self.status.value,
            "action": self.action.value,
            "confidence": self.confidence.value,
            "summary": self.summary,
            "reasons": list(self.reasons),
            "risks": [risk.to_dict() for risk in self.risks],
            "agent_views": [view.to_dict() for view in self.agent_views],
            "data_gaps": list(self.data_context.gaps),
        }