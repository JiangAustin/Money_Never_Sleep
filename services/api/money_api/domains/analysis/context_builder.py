"""Build normalized data context for analysis runs."""

from dataclasses import dataclass, field
from typing import Any, Protocol

from money_api.domains.analysis.contracts import DataContext, StockIdentity


class MarketDataProvider(Protocol):
    def get_quote(self, stock: StockIdentity) -> dict[str, Any]: ...
    def get_technicals(self, stock: StockIdentity) -> dict[str, Any]: ...
    def get_fundamentals(self, stock: StockIdentity) -> dict[str, Any]: ...
    def get_news(self, stock: StockIdentity) -> list[dict[str, Any]]: ...


@dataclass
class StaticMarketDataProvider:
    quote: dict[str, Any] = field(default_factory=dict)
    technicals: dict[str, Any] = field(default_factory=dict)
    fundamentals: dict[str, Any] = field(default_factory=dict)
    news: list[dict[str, Any]] = field(default_factory=list)

    def get_quote(self, stock: StockIdentity) -> dict[str, Any]:
        return dict(self.quote)

    def get_technicals(self, stock: StockIdentity) -> dict[str, Any]:
        return dict(self.technicals)

    def get_fundamentals(self, stock: StockIdentity) -> dict[str, Any]:
        return dict(self.fundamentals)

    def get_news(self, stock: StockIdentity) -> list[dict[str, Any]]:
        return list(self.news)


class DataContextBuilder:
    def __init__(self, provider: MarketDataProvider):
        self.provider = provider

    def build(self, stock: StockIdentity) -> DataContext:
        quote = self.provider.get_quote(stock)
        technicals = self.provider.get_technicals(stock)
        fundamentals = self.provider.get_fundamentals(stock)
        news = self.provider.get_news(stock)
        gaps = []
        if not quote:
            gaps.append("quote")
        if not technicals:
            gaps.append("technicals")
        if not fundamentals:
            gaps.append("fundamentals")
        if not news:
            gaps.append("news")
        return DataContext(
            stock=stock,
            quote=quote,
            technicals=technicals,
            fundamentals=fundamentals,
            news=news,
            gaps=gaps,
        )
