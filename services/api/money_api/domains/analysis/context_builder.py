"""Build normalized data context for analysis runs."""

from dataclasses import dataclass, field
from typing import Any, Protocol

from money_api.domains.analysis.contracts import DataContext, StockIdentity
from money_api.domains.market_data.provider_results import ProviderResult


class MarketDataProvider(Protocol):
    """Provider contract returning structured provider results."""

    def get_quote(self, stock: StockIdentity) -> ProviderResult: ...
    def get_technicals(self, stock: StockIdentity) -> ProviderResult: ...
    def get_fundamentals(self, stock: StockIdentity) -> ProviderResult: ...
    def get_news(self, stock: StockIdentity) -> ProviderResult: ...


@dataclass
class StaticMarketDataProvider:
    """Offline deterministic provider whose getters return copied payloads."""

    quote: dict[str, Any] = field(default_factory=dict)
    technicals: dict[str, Any] = field(default_factory=dict)
    fundamentals: dict[str, Any] = field(default_factory=dict)
    news: list[dict[str, Any]] = field(default_factory=list)

    def get_quote(self, stock: StockIdentity) -> ProviderResult:
        quote = dict(self.quote)
        return ProviderResult(kind="quote", source="static", ok=bool(quote), data=quote)

    def get_technicals(self, stock: StockIdentity) -> ProviderResult:
        technicals = dict(self.technicals)
        return ProviderResult(kind="technicals", source="static", ok=bool(technicals), data=technicals)

    def get_fundamentals(self, stock: StockIdentity) -> ProviderResult:
        fundamentals = dict(self.fundamentals)
        return ProviderResult(kind="fundamentals", source="static", ok=bool(fundamentals), data=fundamentals)

    def get_news(self, stock: StockIdentity) -> ProviderResult:
        news = list(self.news)
        return ProviderResult(kind="news", source="static", ok=bool(news), data=news)


class DataContextBuilder:
    def __init__(self, provider: MarketDataProvider):
        self.provider = provider

    def build(self, stock: StockIdentity) -> DataContext:
        """Build context and record provider failures as ordered data gaps."""

        quote_result = self.provider.get_quote(stock)
        technicals_result = self.provider.get_technicals(stock)
        fundamentals_result = self.provider.get_fundamentals(stock)
        news_result = self.provider.get_news(stock)

        quote = quote_result.data if isinstance(quote_result.data, dict) else {}
        technicals = technicals_result.data if isinstance(technicals_result.data, dict) else {}
        fundamentals = fundamentals_result.data if isinstance(fundamentals_result.data, dict) else {}
        news = news_result.data if isinstance(news_result.data, list) else []

        diagnostics = [
            quote_result.to_diagnostic(),
            technicals_result.to_diagnostic(),
            fundamentals_result.to_diagnostic(),
            news_result.to_diagnostic(),
        ]

        gaps = []
        for result, data in (
            (quote_result, quote),
            (technicals_result, technicals),
            (fundamentals_result, fundamentals),
            (news_result, news),
        ):
            if (not result.ok or not data) and result.gap_name not in gaps:
                gaps.append(result.gap_name)

        return DataContext(
            stock=stock,
            quote=quote,
            technicals=technicals,
            fundamentals=fundamentals,
            news=news,
            gaps=gaps,
            diagnostics=diagnostics,
        )
