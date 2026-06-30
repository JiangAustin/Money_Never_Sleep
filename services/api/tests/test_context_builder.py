from money_api.domains.analysis.context_builder import DataContextBuilder, StaticMarketDataProvider
from money_api.domains.analysis.contracts import StockIdentity


def test_build_context_collects_available_data() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    provider = StaticMarketDataProvider(
        quote={"price": 1688.0},
        technicals={"ma5": 1660.0},
        fundamentals={"pe_ttm": 28.5},
        news=[{"title": "业绩稳定"}],
    )

    context = DataContextBuilder(provider).build(stock)

    assert context.stock == stock
    assert context.quote["price"] == 1688.0
    assert context.technicals["ma5"] == 1660.0
    assert context.fundamentals["pe_ttm"] == 28.5
    assert context.news == [{"title": "业绩稳定"}]
    assert context.gaps == []


def test_build_context_records_data_gaps() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    provider = StaticMarketDataProvider(quote={"price": 1688.0})

    context = DataContextBuilder(provider).build(stock)

    assert context.gaps == ["technicals", "fundamentals", "news"]
