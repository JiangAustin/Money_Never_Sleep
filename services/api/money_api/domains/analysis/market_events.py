"""Structured market event extraction for the first A-share event slice."""

from __future__ import annotations

from typing import Any

from money_api.domains.analysis.contracts import (
    MarketEvent,
    MarketEventType,
    _market_event_evidence_scope_from_match,
    _market_event_evidence_excerpt,
    _market_event_priority_from_type,
)


_EVENT_RULES: list[tuple[MarketEventType, tuple[str, ...], str]] = [
    (
        MarketEventType.EARNINGS_FORECAST,
        ("业绩预告", "业绩快报", "预增", "预减", "扭亏", "盈利预告"),
        "识别为业绩预告类事件，属于高优先级基本面信号。",
    ),
    (
        MarketEventType.SHARE_REDUCTION,
        ("减持", "拟减持", "减持计划"),
        "识别为减持类事件，属于高优先级供给侧信号。",
    ),
    (
        MarketEventType.GUARANTEE,
        ("担保", "对外担保"),
        "识别为担保类事件，属于高优先级风险事件。",
    ),
    (
        MarketEventType.SHARE_UNLOCK,
        ("解禁", "限售股解禁", "解除限售"),
        "识别为解禁类事件，属于高优先级供给侧事件。",
    ),
    (
        MarketEventType.SHARE_REPURCHASE,
        ("股份回购", "回购方案", "拟回购"),
        "识别为回购类事件，属于高优先级股东回报信号。",
    ),
    (
        MarketEventType.SHARE_INCREASE,
        ("增持", "拟增持", "增持计划", "股东增持"),
        "识别为增持类事件，属于高优先级股东增持信号。",
    ),
    (
        MarketEventType.SHARE_PLEDGE,
        ("股权质押", "质押进展", "质押公告"),
        "识别为股权质押类事件，属于高优先级风险事件。",
    ),
]


def build_structured_market_events(items: list[dict[str, Any]]) -> list[MarketEvent]:
    """Extract the first thin structured event stream from news/bulletin items."""

    events: list[MarketEvent] = []
    seen: set[tuple[str, str, str, str]] = set()

    for item in items:
        for event in _classify_item(item):
            signature = (event.event_type.value, event.title, event.source, event.time)
            if signature in seen:
                continue
            seen.add(signature)
            events.append(event)

    return events


def _classify_item(item: dict[str, Any]) -> list[MarketEvent]:
    title = str(item.get("title", "")).strip()
    content = str(item.get("content", "")).strip()
    source = str(item.get("source", "")).strip()
    time = str(item.get("time", "")).strip()
    url = str(item.get("url", "")).strip()
    searchable_text = f"{title} {content}".strip()
    if not searchable_text:
        return []

    events: list[MarketEvent] = []
    for event_type, keywords, summary in _EVENT_RULES:
        title_matches = [keyword for keyword in keywords if keyword in title]
        content_matches = [keyword for keyword in keywords if keyword in content]
        matched_keywords = [keyword for keyword in keywords if keyword in searchable_text]
        if not matched_keywords:
            continue
        confidence = "high" if title_matches else "medium"
        events.append(
            MarketEvent(
                event_type=event_type,
                title=title,
                source=source,
                summary=summary,
                confidence=confidence,
                priority=_market_event_priority_from_type(event_type),
                evidence_scope=_market_event_evidence_scope_from_match(bool(title_matches), bool(content_matches)),
                evidence_excerpt=_market_event_evidence_excerpt(title, content, bool(title_matches), content_matches),
                time=time,
                content=content,
                url=url,
                matched_keywords=matched_keywords,
            )
        )

    return events
