import pytest

from money_api.domains.market_data.resolver import StockResolver, normalize_stock_code


def test_normalize_a_share_code_formats() -> None:
    assert normalize_stock_code("600519") == "600519"
    assert normalize_stock_code("SH600519") == "600519"
    assert normalize_stock_code("600519.SH") == "600519"
    assert normalize_stock_code("sz000001") == "000001"


def test_resolve_chinese_name_from_injected_map() -> None:
    resolver = StockResolver(name_map={"贵州茅台": "600519"})

    stock = resolver.resolve("贵州茅台")

    assert stock.code == "600519"
    assert stock.name == "贵州茅台"
    assert stock.market == "cn"


def test_reject_unknown_symbol() -> None:
    resolver = StockResolver(name_map={})

    with pytest.raises(ValueError, match="无法解析股票"):
        resolver.resolve("不存在股票")