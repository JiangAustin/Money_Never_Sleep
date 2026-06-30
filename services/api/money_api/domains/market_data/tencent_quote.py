"""Tencent quote parsing and provider implementation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from urllib import request

from money_api.domains.analysis.contracts import StockIdentity
from money_api.domains.market_data.provider_results import ProviderResult


def get_tencent_market_prefix(code: str) -> str:
    if code.startswith(("6", "9")):
        return "sh"
    if code.startswith("8"):
        return "bj"
    return "sz"


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_tencent_quote_line(code: str, raw_line: str) -> dict[str, object]:
    if "=\"" not in raw_line or not raw_line.strip().endswith("\";"):
        raise ValueError(f"无法解析腾讯行情: {code}")

    start = raw_line.find('"')
    end = raw_line.rfind('"')
    if start < 0 or end <= start:
        raise ValueError(f"无法解析腾讯行情: {code}")

    payload = raw_line[start + 1 : end]
    values = payload.split("~")
    if len(values) <= 48:
        raise ValueError(f"无法解析腾讯行情: {code}")

    quote = {
        "code": code,
        "name": values[1] or code,
        "price": _to_float(values[3]),
        "last_close": _to_float(values[4]),
        "open": _to_float(values[5]),
        "change_pct": _to_float(values[32]),
        "high": _to_float(values[33]),
        "low": _to_float(values[34]),
        "turnover_pct": _to_float(values[38]),
        "pe_ttm": _to_float(values[39]),
        "market_cap": _to_float(values[44]),
        "pb": _to_float(values[46]),
        "limit_up": _to_float(values[47]),
        "limit_down": _to_float(values[48]),
        "source": "tencent",
    }
    return quote


def _default_transport(url: str, timeout_s: float) -> str:
    with request.urlopen(url, timeout=timeout_s) as response:
        raw = response.read()
    return raw.decode("gbk", errors="replace")


@dataclass
class TencentQuoteProvider:
    transport: Callable[[str], str] | None = None
    timeout_s: float = 10.0

    def get_quote(self, stock: StockIdentity) -> ProviderResult:
        prefix = get_tencent_market_prefix(stock.code)
        url = f"https://qt.gtimg.cn/q={prefix}{stock.code}"
        fetch = self.transport or (lambda target: _default_transport(target, self.timeout_s))
        fetched_at = datetime.now(timezone.utc).isoformat()

        try:
            raw_line = fetch(url)
            quote = parse_tencent_quote_line(stock.code, raw_line)
            return ProviderResult(
                kind="quote",
                source="tencent",
                ok=bool(quote.get("price") is not None),
                data=quote,
                fetched_at=fetched_at,
            )
        except Exception as exc:  # pragma: no cover - network failures vary by env
            return ProviderResult(
                kind="quote",
                source="tencent",
                ok=False,
                data={},
                error_type=type(exc).__name__,
                error_message=str(exc),
                fetched_at=fetched_at,
            )
