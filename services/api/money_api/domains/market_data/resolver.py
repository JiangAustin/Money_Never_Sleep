"""Stock symbol resolver for the first Money_Never_sleep slice."""

import re

from money_api.domains.analysis.contracts import StockIdentity


def normalize_stock_code(raw_symbol: str) -> str:
    symbol = raw_symbol.strip().upper()
    for suffix in (".SH", ".SZ", ".BJ"):
        if symbol.endswith(suffix):
            symbol = symbol[: -len(suffix)]
            break
    for prefix in ("SH", "SZ", "BJ"):
        if symbol.startswith(prefix):
            symbol = symbol[len(prefix) :]
            break
    if re.fullmatch(r"\d{6}", symbol):
        return symbol
    raise ValueError(f"无法解析股票: {raw_symbol}")


class StockResolver:
    def __init__(self, name_map: dict[str, str] | None = None):
        self.name_map = name_map or {}

    def resolve(self, raw_symbol: str) -> StockIdentity:
        cleaned = raw_symbol.strip()
        if not cleaned:
            raise ValueError("无法解析股票: 输入为空")
        if cleaned in self.name_map:
            return StockIdentity(code=self.name_map[cleaned], name=cleaned, market="cn")
        code = normalize_stock_code(cleaned)
        return StockIdentity(code=code, name=code, market="cn")