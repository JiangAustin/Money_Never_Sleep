"""Sina stock bulletin headline provider for runtime analysis context."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Callable
from urllib import request

from money_api.domains.analysis.contracts import StockIdentity
from money_api.domains.market_data.provider_results import ProviderResult


def parse_sina_bulletin_html(html: str) -> list[dict[str, str]]:
    rows = re.findall(r"(\d{4}-\d{2}-\d{2})\s*<a[^>]+href=['\"]([^'\"]+)['\"][^>]*>([^<]+)</a>", html)
    return [
        {
            "title": title.strip(),
            "content": "",
            "time": date_text,
            "source": "新浪公告",
            "url": url.strip(),
        }
        for date_text, url, title in rows
    ]


def _default_transport(url: str, timeout_s: float) -> str:
    req = request.Request(
        url,
        headers={
            "Referer": "https://finance.sina.com.cn/",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
            ),
        },
    )
    with request.urlopen(req, timeout=timeout_s) as response:
        raw = response.read()
    return raw.decode("gb2312", errors="replace")


def _get_sina_symbol(code: str) -> str:
    return f"sh{code}" if code.startswith(("6", "9")) else f"sz{code}"


@dataclass
class SinaBulletinProvider:
    transport: Callable[[str], str] | None = None
    timeout_s: float = 15.0

    def get_news(self, stock: StockIdentity) -> ProviderResult:
        fetched_at = datetime.now(timezone.utc).isoformat()
        url = f"https://vip.stock.finance.sina.com.cn/corp/go.php/vCB_AllBulletin/stockid/{stock.code}.phtml?symbol={_get_sina_symbol(stock.code)}"
        fetch = self.transport or (lambda target: _default_transport(target, self.timeout_s))
        try:
            articles = parse_sina_bulletin_html(fetch(url))
            return ProviderResult(
                kind="news",
                source="sina-bulletin",
                ok=bool(articles),
                data=articles,
                fetched_at=fetched_at,
            )
        except Exception as exc:  # pragma: no cover - network failures vary by env
            return ProviderResult(
                kind="news",
                source="sina-bulletin",
                ok=False,
                data=[],
                error_type=type(exc).__name__,
                error_message=str(exc),
                fetched_at=fetched_at,
            )