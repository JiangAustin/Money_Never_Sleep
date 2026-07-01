from money_api.domains.analysis.contracts import StockIdentity
from money_api.domains.market_data.cls_market_flash import ClsMarketFlashProvider, parse_cls_market_flash_payload


def test_parse_cls_market_flash_payload_returns_normalized_articles() -> None:
    payload = {
        "data": {
            "roll_data": [
                {
                    "title": "央行公开市场操作",
                    "content": "今日开展逆回购操作",
                    "ctime": "1782869400",
                }
            ]
        }
    }

    articles = parse_cls_market_flash_payload(payload)

    assert articles == [
        {
            "title": "央行公开市场操作",
            "content": "今日开展逆回购操作",
            "time": "2026-07-01 09:30",
            "source": "CLS Wire",
            "url": "",
        }
    ]


def test_cls_market_flash_provider_returns_provider_result() -> None:
    provider = ClsMarketFlashProvider(transport=lambda url: {"data": {"roll_data": [{"title": "央行公开市场操作", "brief": "今日开展逆回购操作", "ctime": "1782869400"}]}})

    result = provider.get_news(StockIdentity(code="600519", name="贵州茅台"))

    assert result.ok is True
    assert result.source == "cls"
    assert result.data[0]["source"] == "CLS Wire"


def test_cls_market_flash_provider_handles_transport_failure() -> None:
    provider = ClsMarketFlashProvider(transport=lambda url: (_ for _ in ()).throw(RuntimeError("boom")))

    result = provider.get_news(StockIdentity(code="600519", name="贵州茅台"))

    assert result.ok is False
    assert result.data == []
    assert result.error_type == "RuntimeError"