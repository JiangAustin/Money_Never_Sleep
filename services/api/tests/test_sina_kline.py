from money_api.domains.analysis.contracts import BacktestPricePoint, StockIdentity
from money_api.domains.market_data.sina_kline import SinaKLineProvider, get_sina_market_symbol, parse_sina_kline_payload


def test_get_sina_market_symbol() -> None:
    assert get_sina_market_symbol("600519") == "sh600519"
    assert get_sina_market_symbol("000001") == "sz000001"
    assert get_sina_market_symbol("830000") == "bj830000"


def test_parse_sina_kline_payload() -> None:
    raw = '[{"day":"2026-07-01","close":"100.00"},{"day":"2026-07-02","close":"108.00"}]'

    points = parse_sina_kline_payload(raw, limit=10)

    assert points == [
        BacktestPricePoint(date="2026-07-01", close=100.0),
        BacktestPricePoint(date="2026-07-02", close=108.0),
    ]


def test_sina_kline_provider_success() -> None:
    def transport(url: str) -> str:
        assert "sh600519" in url
        return '[{"day":"2026-07-01","close":"100.00"},{"day":"2026-07-02","close":"108.00"}]'

    result = SinaKLineProvider(transport=transport).get_price_series(StockIdentity(code="600519", name="贵州茅台"), limit=2)

    assert result.ok is True
    assert result.kind == "price_series"
    assert result.source == "sina"
    assert result.data[0].date == "2026-07-01"


def test_sina_kline_provider_failure() -> None:
    def transport(url: str) -> str:
        raise TimeoutError("timeout")

    result = SinaKLineProvider(transport=transport).get_price_series(StockIdentity(code="600519", name="贵州茅台"), limit=2)

    assert result.ok is False
    assert result.error_type == "TimeoutError"
    assert result.error_message == "timeout"
