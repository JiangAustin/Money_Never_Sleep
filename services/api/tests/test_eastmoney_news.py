from money_api.domains.analysis.contracts import StockIdentity
from money_api.domains.market_data.cls_market_flash import ClsMarketFlashProvider
from money_api.domains.market_data.eastmoney_news import CompositeNewsProvider, EastmoneyNewsProvider, parse_eastmoney_news_jsonp


def test_parse_eastmoney_news_jsonp_returns_normalized_articles() -> None:
    payload = (
        'callback({"result":{"cmsArticleWebOld":[{"title":"茅台业绩稳健","content":"季度表现稳定",'
        '"date":"2026-07-01 09:30:00","mediaName":"东方财富","url":"https://example.com/news/1"}]}})'
    )

    articles = parse_eastmoney_news_jsonp(payload)

    assert articles == [
        {
            "title": "茅台业绩稳健",
            "content": "季度表现稳定",
            "time": "2026-07-01 09:30:00",
            "source": "东方财富",
            "url": "https://example.com/news/1",
        }
    ]


def test_eastmoney_news_provider_returns_provider_result() -> None:
    payload = (
        'callback({"result":{"cmsArticleWebOld":[{"title":"茅台业绩稳健","content":"季度表现稳定",'
        '"date":"2026-07-01 09:30:00","mediaName":"东方财富","url":"https://example.com/news/1"}]}})'
    )
    provider = EastmoneyNewsProvider(transport=lambda url: payload)

    result = provider.get_news(StockIdentity(code="600519", name="贵州茅台"))

    assert result.ok is True
    assert result.source == "eastmoney"
    assert result.data[0]["title"] == "茅台业绩稳健"


def test_eastmoney_news_provider_handles_transport_failure() -> None:
    provider = EastmoneyNewsProvider(transport=lambda url: (_ for _ in ()).throw(RuntimeError("boom")))

    result = provider.get_news(StockIdentity(code="600519", name="贵州茅台"))

    assert result.ok is False
    assert result.data == []
    assert result.error_type == "RuntimeError"
    assert result.error_message == "boom"


def test_composite_news_provider_merges_and_deduplicates_articles() -> None:
    stock_news = EastmoneyNewsProvider(
        transport=lambda url: (
            'callback({"result":{"cmsArticleWebOld":[{"title":"茅台业绩稳健","content":"季度表现稳定",'
            '"date":"2026-07-01 09:30:00","mediaName":"东方财富","url":"https://example.com/news/1"}]}})'
        )
    )
    flash_news = ClsMarketFlashProvider(
        transport=lambda url: {"data": {"roll_data": [{"title": "央行公开市场操作", "brief": "今日开展逆回购操作", "ctime": "1782879000"}]}}
    )
    provider = CompositeNewsProvider([stock_news, flash_news])

    result = provider.get_news(StockIdentity(code="600519", name="贵州茅台"))

    assert result.ok is True
    assert result.source == "eastmoney+cls"
    assert [item["source"] for item in result.data] == ["东方财富", "CLS Wire"]