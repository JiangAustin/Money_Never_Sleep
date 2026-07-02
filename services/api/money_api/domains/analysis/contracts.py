"""Stable analysis domain contracts for Money_Never_sleep workflows."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from money_api.domains.analysis.provenance import collect_data_sources, infer_engine_mode, infer_engine_source


class AnalysisStatus(str, Enum):
    """Lifecycle states for an analysis task as it moves toward a report."""

    QUEUED = "queued"
    COLLECTING_DATA = "collecting_data"
    QUICK_SCREENING = "quick_screening"
    DEEP_ANALYSIS = "deep_analysis"
    RISK_REVIEW = "risk_review"
    REPORT_READY = "report_ready"
    FAILED = "failed"
    CANCELLED = "cancelled"


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


class MarketEventType(str, Enum):
    """Structured event categories used by the first A-share event slice."""

    EARNINGS_FORECAST = "earnings_forecast"
    SHARE_REDUCTION = "share_reduction"
    GUARANTEE = "guarantee"
    SHARE_UNLOCK = "share_unlock"
    SHARE_REPURCHASE = "share_repurchase"
    SHARE_PLEDGE = "share_pledge"
    SHARE_INCREASE = "share_increase"
    OTHER = "other"


def _market_event_type_from_value(value: Any) -> MarketEventType:
    try:
        return MarketEventType(str(value))
    except ValueError:
        return MarketEventType.OTHER


def _market_event_priority_from_type(event_type: MarketEventType) -> str:
    if event_type in {
        MarketEventType.EARNINGS_FORECAST,
        MarketEventType.SHARE_REDUCTION,
        MarketEventType.GUARANTEE,
        MarketEventType.SHARE_REPURCHASE,
        MarketEventType.SHARE_INCREASE,
        MarketEventType.SHARE_PLEDGE,
    }:
        return "high"
    if event_type == MarketEventType.SHARE_UNLOCK:
        return "medium"
    return "low"


def _market_event_evidence_scope_from_match(title_matched: bool, content_matched: bool) -> str:
    if title_matched and content_matched:
        return "title+content"
    if title_matched:
        return "title"
    if content_matched:
        return "content"
    return "unknown"


def _market_event_evidence_excerpt(
    title: str,
    content: str,
    title_matched: bool,
    content_matches: list[str],
) -> str:
    if content_matches:
        keyword = content_matches[0]
        if not content:
            return title
        index = content.find(keyword)
        if index < 0:
            return content[:60]
        start = max(0, index - 12)
        end = min(len(content), index + len(keyword) + 12)
        excerpt = content[start:end].strip()
        if start > 0:
            excerpt = f"…{excerpt}"
        if end < len(content):
            excerpt = f"{excerpt}…"
        return excerpt
    if title_matched:
        return title
    return ""


def _data_trust_level_from_score(score: int) -> str:
    if score >= 80:
        return "high"
    if score >= 55:
        return "medium"
    return "low"


def _engine_cost_tier(engine_source: str, engine_mode: str) -> str:
    if engine_mode == "tradingagents":
        return "high" if engine_source != "fake-tradingagents" else "low"
    if engine_mode == "auto":
        return "high" if engine_source == "mock" else "low"
    return "low"


def _engine_cost_rank(cost_tier: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(cost_tier, 0)


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
class InvestmentPlan:
    direction: DecisionAction
    target_position_pct: float
    entry_conditions: list[str]
    exit_conditions: list[str]
    stop_loss_pct: float
    take_profit_pct: float
    observation_window: str
    review_conditions: list[str]
    rationale: list[str]
    risk_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "direction": self.direction.value,
            "target_position_pct": self.target_position_pct,
            "entry_conditions": list(self.entry_conditions),
            "exit_conditions": list(self.exit_conditions),
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct,
            "observation_window": self.observation_window,
            "review_conditions": list(self.review_conditions),
            "rationale": list(self.rationale),
            "risk_notes": list(self.risk_notes),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "InvestmentPlan":
        return cls(
            direction=DecisionAction(str(payload.get("direction", DecisionAction.WATCH.value))),
            target_position_pct=max(0, float(payload.get("target_position_pct", 0))),
            entry_conditions=[str(item) for item in payload.get("entry_conditions", [])],
            exit_conditions=[str(item) for item in payload.get("exit_conditions", [])],
            stop_loss_pct=max(0, float(payload.get("stop_loss_pct", 0))),
            take_profit_pct=max(0, float(payload.get("take_profit_pct", 0))),
            observation_window=str(payload.get("observation_window", "")),
            review_conditions=[str(item) for item in payload.get("review_conditions", [])],
            rationale=[str(item) for item in payload.get("rationale", [])],
            risk_notes=[str(item) for item in payload.get("risk_notes", [])],
        )


@dataclass(frozen=True)
class DataTrustScore:
    score: int
    level: str
    summary: str
    signals: list[str]
    penalties: list[str]
    data_sources: list[str]
    data_gaps: list[str]
    diagnostics_ok: int
    diagnostics_failed: int
    engine_source: str
    engine_mode: str
    fallback_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "level": self.level,
            "summary": self.summary,
            "signals": list(self.signals),
            "penalties": list(self.penalties),
            "data_sources": list(self.data_sources),
            "data_gaps": list(self.data_gaps),
            "diagnostics_ok": self.diagnostics_ok,
            "diagnostics_failed": self.diagnostics_failed,
            "engine_source": self.engine_source,
            "engine_mode": self.engine_mode,
            "fallback_reason": self.fallback_reason,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DataTrustScore":
        return cls(
            score=max(0, min(100, int(payload.get("score", 0)))),
            level=str(payload.get("level", "low")),
            summary=str(payload.get("summary", "")),
            signals=[str(item) for item in payload.get("signals", [])],
            penalties=[str(item) for item in payload.get("penalties", [])],
            data_sources=[str(item) for item in payload.get("data_sources", [])],
            data_gaps=[str(item) for item in payload.get("data_gaps", [])],
            diagnostics_ok=max(0, int(payload.get("diagnostics_ok", 0))),
            diagnostics_failed=max(0, int(payload.get("diagnostics_failed", 0))),
            engine_source=str(payload.get("engine_source", "")),
            engine_mode=str(payload.get("engine_mode", "")),
            fallback_reason=str(payload.get("fallback_reason")) if payload.get("fallback_reason") is not None else None,
        )

    @classmethod
    def from_report(cls, report: Any) -> "DataTrustScore":
        data_sources = [str(item) for item in getattr(report, "data_sources", [])]
        diagnostics = list(getattr(report.data_context, "diagnostics", []))
        data_gaps = [str(item) for item in getattr(report.data_context, "gaps", [])]
        diagnostics_ok = sum(1 for item in diagnostics if item.get("ok", False))
        diagnostics_failed = max(0, len(diagnostics) - diagnostics_ok)
        signals: list[str] = []
        penalties: list[str] = []
        score = 100

        real_sources = [source for source in data_sources if source not in {"static", "mock", "local-mock"}]
        if real_sources:
            signals.append(f"真实来源：{'、'.join(real_sources)}")
        if data_sources:
            signals.append(f"数据来源数：{len(data_sources)}")
        else:
            penalties.append("未识别到数据来源")
            score -= 25

        if "static" in data_sources or "local-mock" in data_sources:
            penalties.append("包含静态或离线来源")
            score -= 15

        if data_gaps:
            penalties.append(f"存在 {len(data_gaps)} 个数据缺口")
            score -= min(20, len(data_gaps) * 6)

        if diagnostics_failed:
            penalties.append(f"{diagnostics_failed} 条诊断失败")
            score -= min(20, diagnostics_failed * 7)
        if diagnostics_ok:
            signals.append(f"{diagnostics_ok} 条诊断成功")

        fallback_reason = getattr(report, "fallback_reason", None)
        if fallback_reason:
            penalties.append("存在引擎回退")
            score -= 20

        engine_source = str(getattr(report, "engine_source", ""))
        engine_mode = str(getattr(report, "engine_mode", ""))
        if engine_source == "mock":
            penalties.append("使用 mock 引擎")
            score -= 10
        elif engine_source == "fake-tradingagents":
            signals.append("引擎为 fake-tradingagents")

        score = max(0, min(100, score))
        level = _data_trust_level_from_score(score)
        summary = f"数据可信度{ {'high': '高', 'medium': '中', 'low': '低'}[level] }，得分 {score}/100。"
        return cls(
            score=score,
            level=level,
            summary=summary,
            signals=signals,
            penalties=penalties,
            data_sources=data_sources,
            data_gaps=data_gaps,
            diagnostics_ok=diagnostics_ok,
            diagnostics_failed=diagnostics_failed,
            engine_source=engine_source,
            engine_mode=engine_mode,
            fallback_reason=fallback_reason,
        )


@dataclass(frozen=True)
class EngineTelemetry:
    runtime_ms: int
    execution_path: str
    cost_tier: str
    estimated_request_count: int
    engine_source: str
    engine_mode: str
    failure_type: str | None
    failure_reason: str | None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime_ms": self.runtime_ms,
            "execution_path": self.execution_path,
            "cost_tier": self.cost_tier,
            "estimated_request_count": self.estimated_request_count,
            "engine_source": self.engine_source,
            "engine_mode": self.engine_mode,
            "failure_type": self.failure_type,
            "failure_reason": self.failure_reason,
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EngineTelemetry":
        return cls(
            runtime_ms=max(0, int(payload.get("runtime_ms", 0))),
            execution_path=str(payload.get("execution_path", "unknown")),
            cost_tier=str(payload.get("cost_tier", "low")),
            estimated_request_count=max(0, int(payload.get("estimated_request_count", 0))),
            engine_source=str(payload.get("engine_source", "")),
            engine_mode=str(payload.get("engine_mode", "")),
            failure_type=str(payload.get("failure_type")) if payload.get("failure_type") is not None else None,
            failure_reason=str(payload.get("failure_reason")) if payload.get("failure_reason") is not None else None,
            notes=[str(item) for item in payload.get("notes", [])],
        )

    @classmethod
    def from_report(cls, report: Any, runtime_ms: int) -> "EngineTelemetry":
        engine_source = str(getattr(report, "engine_source", ""))
        engine_mode = str(getattr(report, "engine_mode", ""))
        failure_reason = getattr(report, "fallback_reason", None)
        failure_type = "fallback" if failure_reason else None
        execution_path = "quick" if engine_mode == "quick-screening" else "fallback" if failure_reason else "primary"
        cost_tier = _engine_cost_tier(engine_source, engine_mode)
        estimated_request_count = 1 + (1 if execution_path == "fallback" else 0)
        notes: list[str] = []
        if execution_path == "quick":
            notes.append("未触发深度投研引擎")
        elif execution_path == "fallback":
            notes.append("主引擎失败后已回退")
        elif engine_source == "mock":
            notes.append("使用 mock 引擎")
        elif engine_source == "fake-tradingagents":
            notes.append("使用 fake tradingagents 运行器")
        return cls(
            runtime_ms=max(0, runtime_ms),
            execution_path=execution_path,
            cost_tier=cost_tier,
            estimated_request_count=estimated_request_count,
            engine_source=engine_source,
            engine_mode=engine_mode,
            failure_type=failure_type,
            failure_reason=str(failure_reason) if failure_reason is not None else None,
            notes=notes,
        )


@dataclass(frozen=True)
class EngineCostGuardrail:
    status: str
    summary: str
    alerts: list[str]
    max_runtime_ms: int
    max_request_count: int
    max_cost_tier: str
    runtime_ms: int
    estimated_request_count: int
    cost_tier: str
    engine_source: str
    engine_mode: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "summary": self.summary,
            "alerts": list(self.alerts),
            "max_runtime_ms": self.max_runtime_ms,
            "max_request_count": self.max_request_count,
            "max_cost_tier": self.max_cost_tier,
            "runtime_ms": self.runtime_ms,
            "estimated_request_count": self.estimated_request_count,
            "cost_tier": self.cost_tier,
            "engine_source": self.engine_source,
            "engine_mode": self.engine_mode,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EngineCostGuardrail":
        return cls(
            status=str(payload.get("status", "ok")),
            summary=str(payload.get("summary", "")),
            alerts=[str(item) for item in payload.get("alerts", [])],
            max_runtime_ms=max(0, int(payload.get("max_runtime_ms", 0))),
            max_request_count=max(0, int(payload.get("max_request_count", 0))),
            max_cost_tier=str(payload.get("max_cost_tier", "low")),
            runtime_ms=max(0, int(payload.get("runtime_ms", 0))),
            estimated_request_count=max(0, int(payload.get("estimated_request_count", 0))),
            cost_tier=str(payload.get("cost_tier", "low")),
            engine_source=str(payload.get("engine_source", "")),
            engine_mode=str(payload.get("engine_mode", "")),
        )

    @classmethod
    def from_telemetry(
        cls,
        telemetry: EngineTelemetry,
        max_runtime_ms: int = 5000,
        max_request_count: int = 1,
        max_cost_tier: str = "medium",
    ) -> "EngineCostGuardrail":
        alerts: list[str] = []
        status = "ok"
        if telemetry.runtime_ms > max_runtime_ms:
            alerts.append(f"runtime_ms>{max_runtime_ms}")
        if telemetry.estimated_request_count > max_request_count:
            alerts.append(f"estimated_request_count>{max_request_count}")
        if _engine_cost_rank(telemetry.cost_tier) > _engine_cost_rank(max_cost_tier):
            alerts.append(f"cost_tier>{max_cost_tier}")
        if alerts:
            status = "over_budget"
        if status == "ok" and (
            telemetry.runtime_ms >= int(max_runtime_ms * 0.8) or telemetry.cost_tier == max_cost_tier
        ):
            status = "warn"

        summary = f"引擎成本状态：{status}。"
        if alerts:
            summary = f"引擎已超出预算阈值：{ '、'.join(alerts) }。"
        return cls(
            status=status,
            summary=summary,
            alerts=alerts,
            max_runtime_ms=max_runtime_ms,
            max_request_count=max_request_count,
            max_cost_tier=max_cost_tier,
            runtime_ms=telemetry.runtime_ms,
            estimated_request_count=telemetry.estimated_request_count,
            cost_tier=telemetry.cost_tier,
            engine_source=telemetry.engine_source,
            engine_mode=telemetry.engine_mode,
        )


@dataclass(frozen=True)
class MarketEvent:
    """Structured event extracted from news or bulletin titles."""

    event_type: MarketEventType
    title: str
    source: str
    summary: str
    confidence: str = "medium"
    priority: str = "medium"
    evidence_scope: str = "title"
    evidence_excerpt: str = ""
    time: str = ""
    content: str = ""
    url: str = ""
    matched_keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "title": self.title,
            "source": self.source,
            "summary": self.summary,
            "confidence": self.confidence,
            "priority": self.priority,
            "evidence_scope": self.evidence_scope,
            "evidence_excerpt": self.evidence_excerpt,
            "time": self.time,
            "content": self.content,
            "url": self.url,
            "matched_keywords": list(self.matched_keywords),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MarketEvent":
        event_type = _market_event_type_from_value(payload.get("event_type", MarketEventType.OTHER.value))
        return cls(
            event_type=event_type,
            title=str(payload.get("title", "")),
            source=str(payload.get("source", "")),
            summary=str(payload.get("summary", "")),
            confidence=str(payload.get("confidence", "medium")),
            priority=str(payload.get("priority", _market_event_priority_from_type(event_type))),
            evidence_scope=str(payload.get("evidence_scope", "title")),
            evidence_excerpt=str(payload.get("evidence_excerpt", "")),
            time=str(payload.get("time", "")),
            content=str(payload.get("content", "")),
            url=str(payload.get("url", "")),
            matched_keywords=[str(item) for item in payload.get("matched_keywords", [])],
        )


@dataclass(frozen=True)
class BacktestPricePoint:
    date: str
    close: float

    def to_dict(self) -> dict[str, Any]:
        return {"date": self.date, "close": self.close}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BacktestPricePoint":
        return cls(date=str(payload.get("date", "")), close=float(payload.get("close", 0)))


@dataclass(frozen=True)
class BacktestOptions:
    cost_pct: float = 0
    slippage_pct: float = 0
    adjustment: str = "none"

    def to_dict(self) -> dict[str, Any]:
        return {
            "cost_pct": self.cost_pct,
            "slippage_pct": self.slippage_pct,
            "adjustment": self.adjustment,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "BacktestOptions":
        payload = payload or {}
        adjustment = str(payload.get("adjustment", "none"))
        if adjustment not in {"none", "qfq", "hfq"}:
            adjustment = "none"
        return cls(
            cost_pct=max(0, float(payload.get("cost_pct", 0))),
            slippage_pct=max(0, float(payload.get("slippage_pct", 0))),
            adjustment=adjustment,
        )


@dataclass(frozen=True)
class BacktestResult:
    task_id: str
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    return_pct: float
    gross_return_pct: float
    cost_impact_pct: float
    max_drawdown_pct: float
    holding_days: int
    exit_reason: str
    price_path: list[BacktestPricePoint]
    options: BacktestOptions = field(default_factory=BacktestOptions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "entry_date": self.entry_date,
            "exit_date": self.exit_date,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "return_pct": self.return_pct,
            "gross_return_pct": self.gross_return_pct,
            "cost_impact_pct": self.cost_impact_pct,
            "max_drawdown_pct": self.max_drawdown_pct,
            "holding_days": self.holding_days,
            "exit_reason": self.exit_reason,
            "price_path": [point.to_dict() for point in self.price_path],
            "options": self.options.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BacktestResult":
        return cls(
            task_id=str(payload.get("task_id", "")),
            entry_date=str(payload.get("entry_date", "")),
            exit_date=str(payload.get("exit_date", "")),
            entry_price=float(payload.get("entry_price", 0)),
            exit_price=float(payload.get("exit_price", 0)),
            return_pct=float(payload.get("return_pct", 0)),
            gross_return_pct=float(payload.get("gross_return_pct", payload.get("return_pct", 0))),
            cost_impact_pct=float(payload.get("cost_impact_pct", 0)),
            max_drawdown_pct=float(payload.get("max_drawdown_pct", 0)),
            holding_days=int(payload.get("holding_days", 0)),
            exit_reason=str(payload.get("exit_reason", "")),
            price_path=[BacktestPricePoint.from_dict(item) for item in payload.get("price_path", [])],
            options=BacktestOptions.from_dict(payload.get("options")),
        )


@dataclass(frozen=True)
class PortfolioPositionBudget:
    task_id: str
    stock: StockIdentity
    action: DecisionAction
    confidence: ConfidenceLevel
    budget_position_pct: float
    source_position_pct: float
    rules: list[RiskControlRule]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "stock": self.stock.to_dict(),
            "action": self.action.value,
            "confidence": self.confidence.value,
            "budget_position_pct": self.budget_position_pct,
            "source_position_pct": self.source_position_pct,
            "rules": [rule.to_dict() for rule in self.rules],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PortfolioPositionBudget":
        stock_payload = payload.get("stock", {})
        return cls(
            task_id=str(payload.get("task_id", "")),
            stock=StockIdentity(
                code=str(stock_payload.get("code", "")),
                name=str(stock_payload.get("name", "")),
                market=str(stock_payload.get("market", "cn")),
            ),
            action=DecisionAction(str(payload.get("action", DecisionAction.WATCH.value))),
            confidence=ConfidenceLevel(str(payload.get("confidence", ConfidenceLevel.LOW.value))),
            budget_position_pct=float(payload.get("budget_position_pct", 0)),
            source_position_pct=float(payload.get("source_position_pct", 0)),
            rules=[RiskControlRule.from_dict(item) for item in payload.get("rules", [])],
        )


@dataclass(frozen=True)
class PortfolioRiskBudget:
    total_position_pct: float
    cash_reserve_pct: float
    max_total_position_pct: float
    max_single_position_pct: float
    positions: list[PortfolioPositionBudget]
    rules: list[RiskControlRule]
    disclaimer: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_position_pct": self.total_position_pct,
            "cash_reserve_pct": self.cash_reserve_pct,
            "max_total_position_pct": self.max_total_position_pct,
            "max_single_position_pct": self.max_single_position_pct,
            "positions": [position.to_dict() for position in self.positions],
            "rules": [rule.to_dict() for rule in self.rules],
            "disclaimer": self.disclaimer,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PortfolioRiskBudget":
        return cls(
            total_position_pct=float(payload.get("total_position_pct", 0)),
            cash_reserve_pct=float(payload.get("cash_reserve_pct", 1)),
            max_total_position_pct=float(payload.get("max_total_position_pct", 0)),
            max_single_position_pct=float(payload.get("max_single_position_pct", 0)),
            positions=[PortfolioPositionBudget.from_dict(item) for item in payload.get("positions", [])],
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
    events: list[MarketEvent] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stock": self.stock.to_dict(),
            "quote": dict(self.quote),
            "technicals": dict(self.technicals),
            "fundamentals": dict(self.fundamentals),
            "news": list(self.news),
            "events": [event.to_dict() for event in self.events],
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
            events=[MarketEvent.from_dict(item) for item in payload.get("events", [])],
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
    data_sources: list[str] = field(default_factory=list)
    engine_source: str = "mock"
    engine_mode: str = "mock"
    fallback_reason: str | None = None
    risk_controls: RiskControlPlan | None = None
    investment_plan: InvestmentPlan | None = None
    data_trust: DataTrustScore | None = None
    engine_telemetry: EngineTelemetry | None = None
    engine_cost_guardrail: EngineCostGuardrail | None = None

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
            "data_sources": list(self.data_sources) or collect_data_sources(self.data_context.diagnostics),
            "engine_source": self.engine_source,
            "engine_mode": self.engine_mode,
            "fallback_reason": self.fallback_reason,
            "data_context": self.data_context.to_dict(),
            "risk_controls": self.risk_controls.to_dict() if self.risk_controls is not None else None,
            "investment_plan": self.investment_plan.to_dict() if self.investment_plan is not None else None,
            "data_trust": self.data_trust.to_dict() if self.data_trust is not None else None,
            "engine_telemetry": self.engine_telemetry.to_dict() if self.engine_telemetry is not None else None,
            "engine_cost_guardrail": self.engine_cost_guardrail.to_dict() if self.engine_cost_guardrail is not None else None,
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
        investment_plan_payload = payload.get("investment_plan")
        data_trust_payload = payload.get("data_trust")
        engine_telemetry_payload = payload.get("engine_telemetry")
        engine_cost_guardrail_payload = payload.get("engine_cost_guardrail")
        data_sources = [str(item) for item in (payload.get("data_sources") or [])]
        if not data_sources:
            data_sources = collect_data_sources(context_payload.get("diagnostics") or [])
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
            data_sources=data_sources,
            engine_source=infer_engine_source(payload.get("engine_source"), data_sources),
            engine_mode=infer_engine_mode(payload.get("engine_mode"), payload.get("engine_source")),
            fallback_reason=str(payload.get("fallback_reason")) if payload.get("fallback_reason") is not None else None,
            risk_controls=RiskControlPlan.from_dict(risk_controls_payload) if risk_controls_payload else None,
            investment_plan=InvestmentPlan.from_dict(investment_plan_payload) if investment_plan_payload else None,
            data_trust=DataTrustScore.from_dict(data_trust_payload) if data_trust_payload else None,
            engine_telemetry=EngineTelemetry.from_dict(engine_telemetry_payload) if engine_telemetry_payload else None,
            engine_cost_guardrail=EngineCostGuardrail.from_dict(engine_cost_guardrail_payload) if engine_cost_guardrail_payload else None,
        )
