"""Stable analysis domain contracts for Money_Never_sleep workflows."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AnalysisStatus(str, Enum):
    """Lifecycle states for an analysis task as it moves toward a report."""

    QUEUED = "queued"
    COLLECTING_DATA = "collecting_data"
    QUICK_SCREENING = "quick_screening"
    DEEP_ANALYSIS = "deep_analysis"
    RISK_REVIEW = "risk_review"
    REPORT_READY = "report_ready"
    FAILED = "failed"


class DecisionAction(str, Enum):
    """Recommended report actions produced by the analysis workflow."""

    BUY = "buy"
    WATCH = "watch"
    SELL = "sell"
    WAIT = "wait"


class ConfidenceLevel(str, Enum):
    """Confidence levels attached to an analysis recommendation."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class StockIdentity:
    """Identifies the stock being analyzed across market-specific workflows."""

    code: str
    name: str
    market: str = "cn"

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "name": self.name, "market": self.market}


@dataclass(frozen=True)
class RiskFinding:
    """Describes a risk note; level is currently a string whose values are refined by later risk controls."""

    level: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"level": self.level, "message": self.message}


@dataclass(frozen=True)
class RiskControlRule:
    name: str
    level: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "level": self.level, "message": self.message}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RiskControlRule":
        return cls(
            name=str(payload.get("name", "")),
            level=str(payload.get("level", "")),
            message=str(payload.get("message", "")),
        )


@dataclass(frozen=True)
class RiskControlPlan:
    max_position_pct: float
    stop_loss_pct: float
    take_profit_pct: float
    time_horizon: str
    rules: list[RiskControlRule]
    disclaimer: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_position_pct": self.max_position_pct,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct,
            "time_horizon": self.time_horizon,
            "rules": [rule.to_dict() for rule in self.rules],
            "disclaimer": self.disclaimer,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RiskControlPlan":
        return cls(
            max_position_pct=float(payload.get("max_position_pct", 0)),
            stop_loss_pct=float(payload.get("stop_loss_pct", 0)),
            take_profit_pct=float(payload.get("take_profit_pct", 0)),
            time_horizon=str(payload.get("time_horizon", "")),
            rules=[RiskControlRule.from_dict(item) for item in payload.get("rules", [])],
            disclaimer=str(payload.get("disclaimer", "")),
        )


@dataclass(frozen=True)
class AgentView:
    """Captures one analysis agent's conclusion for the final report."""

    agent: str
    conclusion: str

    def to_dict(self) -> dict[str, str]:
        return {"agent": self.agent, "conclusion": self.conclusion}


@dataclass(frozen=True)
class DataContext:
    """Carries collected analysis data, with gaps explicitly recording missing inputs."""

    stock: StockIdentity
    quote: dict[str, Any] = field(default_factory=dict)
    technicals: dict[str, Any] = field(default_factory=dict)
    fundamentals: dict[str, Any] = field(default_factory=dict)
    news: list[dict[str, Any]] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stock": self.stock.to_dict(),
            "quote": dict(self.quote),
            "technicals": dict(self.technicals),
            "fundamentals": dict(self.fundamentals),
            "news": list(self.news),
            "gaps": list(self.gaps),
            "diagnostics": list(self.diagnostics),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DataContext":
        stock_payload = payload.get("stock", {})
        stock = StockIdentity(
            code=str(stock_payload.get("code", "")),
            name=str(stock_payload.get("name", "")),
            market=str(stock_payload.get("market", "cn")),
        )
        return cls(
            stock=stock,
            quote=dict(payload.get("quote", {})),
            technicals=dict(payload.get("technicals", {})),
            fundamentals=dict(payload.get("fundamentals", {})),
            news=list(payload.get("news", [])),
            gaps=list(payload.get("gaps", [])),
            diagnostics=list(payload.get("diagnostics", [])),
        )


@dataclass(frozen=True)
class AnalysisReport:
    """Aggregates the final recommendation, evidence, risks, and source data context."""

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
    risk_controls: RiskControlPlan | None = None

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
            "data_diagnostics": list(self.data_context.diagnostics),
            "data_context": self.data_context.to_dict(),
            "risk_controls": self.risk_controls.to_dict() if self.risk_controls is not None else None,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AnalysisReport":
        stock_payload = payload.get("stock", {})
        stock = StockIdentity(
            code=str(stock_payload.get("code", "")),
            name=str(stock_payload.get("name", "")),
            market=str(stock_payload.get("market", "cn")),
        )
        context_payload = payload.get("data_context") or {
            "stock": stock.to_dict(),
            "gaps": list(payload.get("data_gaps", [])),
            "diagnostics": list(payload.get("data_diagnostics", [])),
        }
        risk_controls_payload = payload.get("risk_controls")
        return cls(
            task_id=str(payload["task_id"]),
            stock=stock,
            status=AnalysisStatus(str(payload["status"])),
            action=DecisionAction(str(payload["action"])),
            confidence=ConfidenceLevel(str(payload["confidence"])),
            summary=str(payload.get("summary", "")),
            reasons=list(payload.get("reasons", [])),
            risks=[
                RiskFinding(level=str(item.get("level", "")), message=str(item.get("message", "")))
                for item in payload.get("risks", [])
            ],
            agent_views=[
                AgentView(agent=str(item.get("agent", "")), conclusion=str(item.get("conclusion", "")))
                for item in payload.get("agent_views", [])
            ],
            data_context=DataContext.from_dict(context_payload),
            risk_controls=RiskControlPlan.from_dict(risk_controls_payload) if risk_controls_payload else None,
        )