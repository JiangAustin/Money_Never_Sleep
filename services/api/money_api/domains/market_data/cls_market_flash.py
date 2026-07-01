"""CLS market flash provider for runtime analysis context."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable
from urllib import parse, request
import json

from money_api.domains.analysis.contracts import StockIdentity
from money_api.domains.market_data.provider_results import ProviderResult


def parse_cls_market_flash_payload(payload: dict[str, Any]) -> list[dict[str, str]]:
    articles = []
    for item in payload.get("data", {}).get("roll_data", []):
        title = str(item.get("title", "") or item.get("brief", ""))
        content = str(item.get("content", "") or item.get("brief", ""))
        ctime = item.get("ctime", "")
        published_at = ""
        if ctime:
            try:
                published_at = datetime.fromtimestamp(int(ctime)).strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError, OSError):
                published_at = str(ctime)
        articles.append(
            {
                "title": title,
                "content": content,
                "time": published_at,
                "source": "CLS Wire",
                "url": "",
            }
        )
    return articles


def _default_transport(url: str, timeout_s: float) -> dict[str, Any]:
    req = request.Request(
        url,
        headers={
            "Referer": "https://www.cls.cn/",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
            ),
        },
    )
    with request.urlopen(req, timeout=timeout_s) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8", errors="replace"))


@dataclass
class ClsMarketFlashProvider:
    transport: Callable[[str], dict[str, Any]] | None = None
    timeout_s: float = 10.0
    limit: int = 5

    def get_news(self, stock: StockIdentity) -> ProviderResult:
        del stock
        fetched_at = datetime.now(timezone.utc).isoformat()
        url = "https://www.cls.cn/nodeapi/telegraphList?" + parse.urlencode({"rn": str(self.limit), "page": "1"})
        fetch = self.transport or (lambda target: _default_transport(target, self.timeout_s))
        try:
            articles = parse_cls_market_flash_payload(fetch(url))
            return ProviderResult(
                kind="news",
                source="cls",
                ok=bool(articles),
                data=articles,
                fetched_at=fetched_at,
            )
        except Exception as exc:  # pragma: no cover - network failures vary by env
            return ProviderResult(
                kind="news",
                source="cls",
                ok=False,
                data=[],
                error_type=type(exc).__name__,
                error_message=str(exc),
                fetched_at=fetched_at,
            )