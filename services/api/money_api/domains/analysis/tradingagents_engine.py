"""TradingAgents engine adapter contracts."""

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Protocol

from money_api.domains.analysis.contracts import DataContext


@dataclass(frozen=True)
class TradingAgentsRunRequest:
    task_id: str
    code: str
    name: str
    market: str
    trade_date: str
    context_snapshot: dict[str, Any]
    diagnostics: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_context(cls, task_id: str, context: DataContext, trade_date: str | None = None) -> "TradingAgentsRunRequest":
        return cls(
            task_id=task_id,
            code=context.stock.code,
            name=context.stock.name,
            market=context.stock.market,
            trade_date=trade_date or date.today().isoformat(),
            context_snapshot={
                "quote": dict(context.quote),
                "technicals": dict(context.technicals),
                "fundamentals": dict(context.fundamentals),
                "news": list(context.news),
                "gaps": list(context.gaps),
            },
            diagnostics=list(context.diagnostics),
        )


@dataclass(frozen=True)
class TradingAgentsRunResult:
    ok: bool
    source: str
    final_decision: str = "WATCH"
    summary: str = ""
    agent_reports: dict[str, str] = field(default_factory=dict)
    raw_state: dict[str, Any] = field(default_factory=dict)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    error_type: str | None = None
    error_message: str | None = None


class TradingAgentsRunner(Protocol):
    def run(self, request: TradingAgentsRunRequest) -> TradingAgentsRunResult: ...


class FakeTradingAgentsRunner:
    def run(self, request: TradingAgentsRunRequest) -> TradingAgentsRunResult:
        return TradingAgentsRunResult(
            ok=True,
            source="fake-tradingagents",
            final_decision="WATCH",
            summary=f"{request.name} fake TradingAgents 分析完成。",
            agent_reports={
                "market": "离线市场分析结果",
                "fundamentals": "离线基本面分析结果",
                "risk": "离线风险辩论结果",
            },
            diagnostics=[{"kind": "deep_engine", "source": "fake-tradingagents", "ok": True}],
        )
