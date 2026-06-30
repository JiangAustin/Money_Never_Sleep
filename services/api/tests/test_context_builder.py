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


def test_build_context_records_all_data_gaps() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    provider = StaticMarketDataProvider()

    context = DataContextBuilder(provider).build(stock)

    assert context.gaps == ["quote", "technicals", "fundamentals", "news"]


def test_static_provider_returns_shallow_copies() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    provider = StaticMarketDataProvider(
        quote={"price": 1688.0},
        technicals={"ma5": 1660.0},
        fundamentals={"pe_ttm": 28.5},
        news=[{"title": "业绩稳定"}],
    )

    first = DataContextBuilder(provider).build(stock)
    first.quote["price"] = 9999.0
    first.technicals["ma5"] = 1.0
    first.fundamentals["pe_ttm"] = 1.0
    first.news.append({"title": "污染项"})

    second = DataContextBuilder(provider).build(stock)

    assert second.quote == {"price": 1688.0}
    assert second.technicals == {"ma5": 1660.0}
    assert second.fundamentals == {"pe_ttm": 28.5}
    assert second.news == [{"title": "业绩稳定"}]
