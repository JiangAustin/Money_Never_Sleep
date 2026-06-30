"""Optional TradingAgents-astock integration runner."""

from collections.abc import Callable
from typing import Any

from money_api.domains.analysis.tradingagents_engine import TradingAgentsRunRequest, TradingAgentsRunResult


class TradingAgentsGraphRunner:
    def __init__(
        self,
        graph_factory: Callable[..., Any] | None = None,
        selected_analysts: list[str] | None = None,
        config: dict[str, Any] | None = None,
        debug: bool = False,
    ):
        self.graph_factory = graph_factory
        self.selected_analysts = selected_analysts or ["market", "news", "fundamentals", "policy", "hot_money", "lockup"]
        self.config = config or {}
        self.debug = debug

    def run(self, request: TradingAgentsRunRequest) -> TradingAgentsRunResult:
        try:
            graph_factory = self.graph_factory or self._load_graph_factory()
            graph = graph_factory(selected_analysts=self.selected_analysts, debug=self.debug, config=self.config)
            final_state, signal = graph.propagate(request.code, request.trade_date)
            return TradingAgentsRunResult(
                ok=True,
                source="tradingagents",
                final_decision=str(signal or final_state.get("final_trade_decision", "WATCH")),
                summary=str(final_state.get("investment_plan") or final_state.get("final_trade_decision") or signal or "TradingAgents 分析完成"),
                agent_reports={
                    "market": str(final_state.get("market_report", "")),
                    "news": str(final_state.get("news_report", "")),
                    "fundamentals": str(final_state.get("fundamentals_report", "")),
                    "policy": str(final_state.get("policy_report", "")),
                    "hot_money": str(final_state.get("hot_money_report", "")),
                    "lockup": str(final_state.get("lockup_report", "")),
                },
                raw_state=dict(final_state),
                diagnostics=[{"kind": "deep_engine", "source": "tradingagents", "ok": True}],
            )
        except Exception as exc:
            return TradingAgentsRunResult(
                ok=False,
                source="tradingagents",
                diagnostics=[{"kind": "deep_engine", "source": "tradingagents", "ok": False}],
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

    def _load_graph_factory(self) -> Callable[..., Any]:
        from tradingagents.graph.trading_graph import TradingAgentsGraph

        return TradingAgentsGraph
