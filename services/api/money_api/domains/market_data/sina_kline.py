"""Sina daily K-line provider for backtest price series."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Callable
from urllib import request

from money_api.domains.analysis.contracts import BacktestPricePoint, StockIdentity
from money_api.domains.market_data.provider_results import ProviderResult


def get_sina_market_symbol(code: str) -> str:
    if code.startswith(("6", "9")):
        return f"sh{code}"
    if code.startswith("8"):
        return f"bj{code}"
    return f"sz{code}"


def parse_sina_kline_payload(raw: str, limit: int) -> list[BacktestPricePoint]:
    payload = json.loads(raw)
    points = []
    for item in payload[-limit:]:
        date = str(item.get("day") or item.get("date") or "")
        close = float(item.get("close", 0))
        if date and close > 0:
            points.append(BacktestPricePoint(date=date, close=close))
    return points


def _default_transport(url: str, timeout_s: float) -> str:
    with request.urlopen(url, timeout=timeout_s) as response:
        return response.read().decode("utf-8", errors="replace")


@dataclass
class SinaKLineProvider:
    transport: Callable[[str], str] | None = None
    timeout_s: float = 10.0

    def get_price_series(self, stock: StockIdentity, limit: int = 60) -> ProviderResult:
        fetched_at = datetime.now(timezone.utc).isoformat()
        symbol = get_sina_market_symbol(stock.code)
        url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=no&datalen={limit}"
        fetch = self.transport or (lambda target: _default_transport(target, self.timeout_s))
        try:
            points = parse_sina_kline_payload(fetch(url), limit=limit)
            return ProviderResult(
                kind="price_series",
                source="sina",
                ok=bool(points),
                data=points,
                fetched_at=fetched_at,
            )
        except Exception as exc:  # pragma: no cover - network failures vary by env
            return ProviderResult(
                kind="price_series",
                source="sina",
                ok=False,
                data=[],
                error_type=type(exc).__name__,
                error_message=str(exc),
                fetched_at=fetched_at,
            )
