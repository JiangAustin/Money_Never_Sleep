"""Optional TradingAgents-astock integration runner."""

from collections.abc import Callable
from pathlib import Path
import sys
from time import perf_counter
from typing import Any

from money_api.core.config import settings
from money_api.domains.analysis.tradingagents_engine import TradingAgentsRunRequest, TradingAgentsRunResult


DEFAULT_SELECTED_ANALYSTS = ["market", "social", "news", "fundamentals", "policy", "hot_money", "lockup"]


class TradingAgentsGraphRunner:
    def __init__(
        self,
        graph_factory: Callable[..., Any] | None = None,
        selected_analysts: list[str] | None = None,
        config: dict[str, Any] | None = None,
        debug: bool = False,
    ):
        self.graph_factory = graph_factory
        self.selected_analysts = selected_analysts or DEFAULT_SELECTED_ANALYSTS
        self.config = config or {}
        self.debug = debug

    def run(self, request: TradingAgentsRunRequest) -> TradingAgentsRunResult:
        started_at = perf_counter()
        config = self._build_config()
        try:
            graph_factory = self.graph_factory or self._load_graph_factory()
            graph = graph_factory(selected_analysts=self.selected_analysts, debug=self.debug, config=config)
            final_state, signal = graph.propagate(request.code, request.trade_date)
            return TradingAgentsRunResult(
                ok=True,
                source="tradingagents",
                final_decision=str(signal or final_state.get("final_trade_decision", "WATCH")),
                summary=self._summary_from_state(final_state, signal),
                agent_reports=self._agent_reports_from_state(final_state),
                raw_state=dict(final_state),
                diagnostics=[self._diagnostic(True, config, request, started_at)],
            )
        except Exception as exc:
            return TradingAgentsRunResult(
                ok=False,
                source="tradingagents",
                diagnostics=[self._diagnostic(False, config, request, started_at, exc)],
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

    def _build_config(self) -> dict[str, Any]:
        config: dict[str, Any] = {}
        if self.graph_factory is None:
            self._ensure_astock_path()
            try:
                from tradingagents.default_config import DEFAULT_CONFIG

                config.update(DEFAULT_CONFIG)
            except Exception:
                config = {}
        config.update(self.config)
        config.setdefault("output_language", "Chinese")
        config.setdefault("max_debate_rounds", 1)
        config.setdefault("max_risk_discuss_rounds", 1)
        config["results_dir"] = settings.tradingagents_results_dir
        config["data_cache_dir"] = settings.tradingagents_cache_dir
        return config

    def _diagnostic(
        self,
        ok: bool,
        config: dict[str, Any],
        request: TradingAgentsRunRequest,
        started_at: float,
        exc: Exception | None = None,
    ) -> dict[str, Any]:
        payload = {
            "kind": "deep_engine",
            "source": "tradingagents",
            "ok": ok,
            "selected_analysts": list(self.selected_analysts),
            "provider": config.get("llm_provider"),
            "deep_model": config.get("deep_think_llm"),
            "quick_model": config.get("quick_think_llm"),
            "results_dir": config.get("results_dir"),
            "cache_dir": config.get("data_cache_dir"),
            "runtime_ms": int((perf_counter() - started_at) * 1000),
            "context_snapshot": dict(request.context_snapshot),
        }
        if exc is not None:
            payload["error_type"] = type(exc).__name__
            payload["error_message"] = str(exc)
        return payload

    def _summary_from_state(self, final_state: dict[str, Any], signal: Any) -> str:
        return str(
            final_state.get("investment_plan")
            or final_state.get("trader_investment_plan")
            or final_state.get("final_trade_decision")
            or signal
            or "TradingAgents 分析完成"
        )

    def _agent_reports_from_state(self, final_state: dict[str, Any]) -> dict[str, str]:
        report_map = {
            "market": "market_report",
            "social": "sentiment_report",
            "news": "news_report",
            "fundamentals": "fundamentals_report",
            "policy": "policy_report",
            "hot_money": "hot_money_report",
            "lockup": "lockup_report",
            "trader": "trader_investment_plan",
            "final_decision": "final_trade_decision",
        }
        reports = {name: str(final_state.get(key, "")) for name, key in report_map.items() if final_state.get(key)}

        debate = final_state.get("investment_debate_state") or {}
        if isinstance(debate, dict):
            reports.update(
                {
                    name: str(value)
                    for name, value in {
                        "bull_researcher": debate.get("bull_history"),
                        "bear_researcher": debate.get("bear_history"),
                        "research_manager": debate.get("judge_decision"),
                    }.items()
                    if value
                }
            )

        risk = final_state.get("risk_debate_state") or {}
        if isinstance(risk, dict):
            reports.update(
                {
                    name: str(value)
                    for name, value in {
                        "aggressive_risk": risk.get("aggressive_history"),
                        "conservative_risk": risk.get("conservative_history"),
                        "neutral_risk": risk.get("neutral_history"),
                        "portfolio_manager": risk.get("judge_decision"),
                    }.items()
                    if value
                }
            )
        return reports

    def _load_graph_factory(self) -> Callable[..., Any]:
        self._ensure_astock_path()
        from tradingagents.graph.trading_graph import TradingAgentsGraph

        return TradingAgentsGraph

    def _ensure_astock_path(self) -> None:
        candidate_path = Path(settings.tradingagents_astock_path).resolve()
        if candidate_path.exists() and str(candidate_path) not in sys.path:
            sys.path.insert(0, str(candidate_path))
