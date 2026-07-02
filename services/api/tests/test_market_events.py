from money_api.domains.analysis.market_events import build_structured_market_events


def test_build_structured_market_events_extracts_priority_event_types() -> None:
    events = build_structured_market_events(
        [
            {"title": "示例公司发布2026年半年度业绩预告", "content": "预计同比增长", "source": "static", "time": "2026-07-01"},
            {"title": "控股股东拟减持不超过1%股份", "content": "减持计划", "source": "static", "time": "2026-07-02"},
            {"title": "非重点新闻", "content": "无结构化关键词", "source": "static"},
        ]
    )

    assert [event.event_type.value for event in events] == ["earnings_forecast", "share_reduction"]
    assert events[0].matched_keywords == ["业绩预告"]
    assert events[0].priority == "high"
    assert events[0].evidence_scope == "title"
    assert events[0].evidence_excerpt == "示例公司发布2026年半年度业绩预告"
    assert events[1].summary.startswith("识别为减持类事件")


def test_build_structured_market_events_deduplicates_repeated_titles() -> None:
    events = build_structured_market_events(
        [
            {"title": "示例公司对外担保进展公告", "content": "", "source": "sina-bulletin", "time": "2026-07-01"},
            {"title": "示例公司对外担保进展公告", "content": "", "source": "sina-bulletin", "time": "2026-07-01"},
        ]
    )

    assert len(events) == 1
    assert events[0].event_type.value == "guarantee"
    assert events[0].priority == "high"
    assert events[0].evidence_scope == "title"
    assert events[0].evidence_excerpt == "示例公司对外担保进展公告"


def test_build_structured_market_events_keeps_multiple_event_types_per_item() -> None:
    events = build_structured_market_events(
        [
            {
                "title": "示例公司发布业绩预告并披露控股股东拟减持计划",
                "content": "预计利润增长，同时控股股东计划减持。",
                "source": "sina-bulletin",
                "time": "2026-07-02",
            }
        ]
    )

    assert [event.event_type.value for event in events] == ["earnings_forecast", "share_reduction"]
    assert events[0].matched_keywords == ["业绩预告"]
    assert events[0].priority == "high"
    assert events[0].evidence_scope == "title"
    assert events[0].evidence_excerpt == "示例公司发布业绩预告并披露控股股东拟减持计划"
    assert events[1].matched_keywords == ["减持", "拟减持", "减持计划"]


def test_build_structured_market_events_extracts_share_repurchase_and_pledge() -> None:
    events = build_structured_market_events(
        [
            {
                "title": "示例公司发布股份回购方案",
                "content": "拟以自有资金回购部分股份",
                "source": "sina-bulletin",
                "time": "2026-07-02",
            },
            {
                "title": "控股股东股权质押进展公告",
                "content": "质押比例上升",
                "source": "sina-bulletin",
                "time": "2026-07-02",
            },
        ]
    )

    assert [event.event_type.value for event in events] == ["share_repurchase", "share_pledge"]
    assert events[0].summary.startswith("识别为回购类事件")
    assert events[1].summary.startswith("识别为股权质押类事件")
    assert events[0].priority == "high"
    assert events[1].priority == "high"
    assert events[0].evidence_scope == "title"
    assert events[1].evidence_scope == "title"
    assert events[0].evidence_excerpt == "示例公司发布股份回购方案"
    assert events[1].evidence_excerpt == "控股股东股权质押进展公告"


def test_build_structured_market_events_extracts_share_increase() -> None:
    events = build_structured_market_events(
        [
            {
                "title": "控股股东拟增持公司股份",
                "content": "计划在未来 6 个月内增持不超过 2% 股份",
                "source": "sina-bulletin",
                "time": "2026-07-04",
            }
        ]
    )

    assert [event.event_type.value for event in events] == ["share_increase"]
    assert events[0].priority == "high"
    assert events[0].evidence_scope == "title+content"
    assert "增持" in events[0].evidence_excerpt


def test_build_structured_market_events_marks_title_and_content_matches() -> None:
    events = build_structured_market_events(
        [
            {
                "title": "示例公司发布业绩预告",
                "content": "公告正文说明业绩预告并预计同比增长",
                "source": "sina-bulletin",
                "time": "2026-07-03",
            }
        ]
    )

    assert len(events) == 1
    assert events[0].evidence_scope == "title+content"
    assert events[0].evidence_excerpt == "公告正文说明业绩预告并预计同比增长"


def test_build_structured_market_events_marks_content_only_matches() -> None:
    events = build_structured_market_events(
        [
            {
                "title": "示例公司公告",
                "content": "控股股东拟减持不超过1%股份",
                "source": "sina-bulletin",
                "time": "2026-07-03",
            }
        ]
    )

    assert [event.event_type.value for event in events] == ["share_reduction"]
    assert events[0].confidence == "medium"
    assert events[0].evidence_scope == "content"
    assert "减持" in events[0].evidence_excerpt
