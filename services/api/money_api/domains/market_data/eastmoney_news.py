"""Eastmoney stock news provider for runtime analysis context."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from urllib import parse, request

from money_api.domains.analysis.contracts import StockIdentity
from money_api.domains.market_data.provider_results import ProviderResult


def parse_eastmoney_news_jsonp(raw_payload: str) -> list[dict[str, str]]:
    start = raw_payload.find("(")
    end = raw_payload.rfind(")")
    if start < 0 or end <= start:
        raise ValueError("无法解析东方财富新闻响应")

    payload = json.loads(raw_payload[start + 1 : end])
    articles = []
    for item in payload.get("result", {}).get("cmsArticleWebOld", []):
        articles.append(
            {
                "title": str(item.get("title", "")),
                "content": str(item.get("content", "")),
                "time": str(item.get("date", "")),
                "source": str(item.get("mediaName", "东方财富")),
                "url": str(item.get("url", "")),
            }
        )
    return articles


def _default_transport(url: str, timeout_s: float) -> str:
    req = request.Request(
        url,
        headers={
            "Referer": "https://so.eastmoney.com/",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
            ),
        },
    )
    with request.urlopen(req, timeout=timeout_s) as response:
        raw = response.read()
    return raw.decode("utf-8", errors="replace")


@dataclass
class EastmoneyNewsProvider:
    transport: Callable[[str], str] | None = None
    timeout_s: float = 15.0
    page_size: int = 10

    def get_news(self, stock: StockIdentity) -> ProviderResult:
        fetched_at = datetime.now(timezone.utc).isoformat()
        param = {
            "uid": "",
            "keyword": stock.code,
            "type": ["cmsArticleWebOld"],
            "client": "web",
            "clientType": "web",
            "clientVersion": "curr",
            "param": {
                "cmsArticleWebOld": {
                    "searchScope": "default",
                    "sort": "default",
                    "pageIndex": 1,
                    "pageSize": self.page_size,
                    "preTag": "",
                    "postTag": "",
                }
            },
        }
        url = "https://search-api-web.eastmoney.com/search/jsonp?" + parse.urlencode(
            {"cb": "callback", "param": json.dumps(param, ensure_ascii=False), "_": "1"}
        )
        fetch = self.transport or (lambda target: _default_transport(target, self.timeout_s))

        try:
            articles = parse_eastmoney_news_jsonp(fetch(url))
            return ProviderResult(
                kind="news",
                source="eastmoney",
                ok=bool(articles),
                data=articles,
                fetched_at=fetched_at,
            )
        except Exception as exc:  # pragma: no cover - network failures vary by env
            return ProviderResult(
                kind="news",
                source="eastmoney",
                ok=False,
                data=[],
                error_type=type(exc).__name__,
                error_message=str(exc),
                fetched_at=fetched_at,
            )