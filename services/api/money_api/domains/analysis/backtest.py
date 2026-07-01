"""Deterministic report backtesting from supplied price series."""

from money_api.domains.analysis.contracts import AnalysisReport, BacktestOptions, BacktestPricePoint, BacktestResult


class SimpleBacktestEngine:
    def run(self, report: AnalysisReport, prices: list[BacktestPricePoint], options: BacktestOptions | None = None) -> BacktestResult:
        options = options or BacktestOptions()
        if report.risk_controls is None:
            raise ValueError("risk_controls are required for backtesting")
        if len(prices) < 2:
            raise ValueError("at least two price points are required")

        entry = prices[0]
        entry_price = entry.close
        if entry_price <= 0:
            raise ValueError("entry price must be positive")

        stop_loss = -abs(report.risk_controls.stop_loss_pct)
        take_profit = abs(report.risk_controls.take_profit_pct)
        exit_point = prices[-1]
        exit_reason = "time_exit"
        max_drawdown_pct = 0.0

        for point in prices[1:]:
            return_pct = self._return_pct(entry_price, point.close)
            max_drawdown_pct = min(max_drawdown_pct, return_pct)
            if return_pct <= stop_loss:
                exit_point = point
                exit_reason = "stop_loss"
                break
            if return_pct >= take_profit:
                exit_point = point
                exit_reason = "take_profit"
                break

        gross_return_pct = self._return_pct(entry_price, exit_point.close)
        return_pct = self._net_return_pct(entry_price, exit_point.close, options)
        holding_days = prices.index(exit_point)
        return BacktestResult(
            task_id=report.task_id,
            entry_date=entry.date,
            exit_date=exit_point.date,
            entry_price=entry_price,
            exit_price=exit_point.close,
            return_pct=return_pct,
            gross_return_pct=gross_return_pct,
            cost_impact_pct=round(return_pct - gross_return_pct, 6),
            max_drawdown_pct=max_drawdown_pct,
            holding_days=holding_days,
            exit_reason=exit_reason,
            price_path=prices[: holding_days + 1],
            options=options,
        )

    def _return_pct(self, entry_price: float, close: float) -> float:
        return round((close - entry_price) / entry_price, 6)

    def _net_return_pct(self, entry_price: float, close: float, options: BacktestOptions) -> float:
        friction = options.cost_pct + options.slippage_pct
        effective_entry = entry_price * (1 + friction)
        effective_exit = close * (1 - friction)
        return round((effective_exit - effective_entry) / effective_entry, 6)
