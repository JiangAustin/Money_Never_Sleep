from money_api.domains.analysis.contracts import StockIdentity
from money_api.domains.market_data.tencent_quote import (
    TencentQuoteProvider,
    get_tencent_market_prefix,
    parse_tencent_quote_line,
)


def test_get_tencent_market_prefix() -> None:
    assert get_tencent_market_prefix("600519") == "sh"
    assert get_tencent_market_prefix("000001") == "sz"
    assert get_tencent_market_prefix("920001") == "sh"
    assert get_tencent_market_prefix("830000") == "bj"


def test_parse_tencent_quote_line() -> None:
    values = [""] * 53
    values[1] = "贵州茅台"
    values[3] = "1688.00"
    values[4] = "1680.00"
    values[5] = "1681.00"
    values[32] = "1.23"
    values[33] = "1700.00"
    values[34] = "1670.00"
    values[38] = "0.56"
    values[39] = "28.50"
    values[44] = "21000.00"
    values[46] = "9.10"
    values[47] = "1848.00"
    values[48] = "1512.00"
    raw = 'v_sh600519="' + "~".join(values) + '";'

    quote = parse_tencent_quote_line("600519", raw)

    assert quote["code"] == "600519"
    assert quote["name"] == "贵州茅台"
    assert quote["price"] == 1688.0
    assert quote["change_pct"] == 1.23
    assert quote["source"] == "tencent"


def test_tencent_quote_provider_uses_injected_transport() -> None:
    def transport(url: str) -> str:
        assert "sh600519" in url
        values = [""] * 53
        values[1] = "贵州茅台"
        values[3] = "1688.00"
        return 'v_sh600519="' + "~".join(values) + '";'

    result = TencentQuoteProvider(transport=transport).get_quote(StockIdentity(code="600519", name="贵州茅台"))

    assert result.ok is True
    assert result.source == "tencent"
    assert result.data["price"] == 1688.0


def test_tencent_quote_provider_returns_failure_result() -> None:
    def transport(url: str) -> str:
        raise TimeoutError("timeout")

    result = TencentQuoteProvider(transport=transport).get_quote(StockIdentity(code="600519", name="贵州茅台"))

    assert result.ok is False
    assert result.error_type == "TimeoutError"
    assert result.error_message == "timeout"
