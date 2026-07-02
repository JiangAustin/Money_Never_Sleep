"""Agent-facing research tools built on top of the live market data bundle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from money_api.domains.analysis.context_builder import DataContextBuilder
from money_api.domains.analysis.contracts import DataContext, StockIdentity
from money_api.domains.analysis.provenance import collect_data_sources
from money_api.domains.market_data.provider_results import ProviderResult


class StockResolverProtocol(Protocol):
    def resolve(self, symbol: str) -> StockIdentity: ...


class MarketDataBundleProtocol(Protocol):
    def get_quote(self, stock: StockIdentity) -> ProviderResult: ...
    def get_technicals(self, stock: StockIdentity) -> ProviderResult: ...
    def get_fundamentals(self, stock: StockIdentity) -> ProviderResult: ...
    def get_news(self, stock: StockIdentity) -> ProviderResult: ...


class ResearchExtrasProtocol(Protocol):
    def get_capital_flow(self, stock: StockIdentity) -> ProviderResult: ...
    def get_longhubang(self, stock: StockIdentity) -> ProviderResult: ...
    def get_unlocks(self, stock: StockIdentity) -> ProviderResult: ...


def _group_sources(diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: list[dict[str, Any]] = []
    for diagnostic in diagnostics:
        grouped.append(
            {
                "kind": diagnostic.get("kind"),
                "source": diagnostic.get("source"),
                "ok": diagnostic.get("ok"),
                "error_message": diagnostic.get("error_message"),
            }
        )
    return grouped


def _provider_result_payload(result: ProviderResult) -> dict[str, Any]:
    payload = result.to_diagnostic()
    payload["data"] = result.data
    return payload


@dataclass(frozen=True)
class ResearchSnapshot:
    stock: StockIdentity
    data_context: DataContext
    data_sources: list[str]
    source_summary: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "stock": self.stock.to_dict(),
            "data_context": self.data_context.to_dict(),
            "data_sources": list(self.data_sources),
            "source_summary": list(self.source_summary),
        }


class ResearchToolService:
    """Expose live stock research inputs as simple callable tools."""

    def __init__(
        self,
        resolver: StockResolverProtocol,
        provider: MarketDataBundleProtocol,
        extras_provider: ResearchExtrasProtocol | None = None,
    ):
        self.resolver = resolver
        self.provider = provider
        self.extras_provider = extras_provider
        self.context_builder = DataContextBuilder(provider)

    def build_context(self, symbol: str) -> ResearchSnapshot:
        stock = self.resolver.resolve(symbol)
        context = self.context_builder.build(stock)
        return ResearchSnapshot(
            stock=stock,
            data_context=context,
            data_sources=collect_data_sources(context.diagnostics),
            source_summary=_group_sources(context.diagnostics),
        )

    def get_quote(self, symbol: str) -> dict[str, Any]:
        stock = self.resolver.resolve(symbol)
        return {
            "stock": stock.to_dict(),
            "result": _provider_result_payload(self.provider.get_quote(stock)),
        }

    def get_technicals(self, symbol: str) -> dict[str, Any]:
        stock = self.resolver.resolve(symbol)
        return {
            "stock": stock.to_dict(),
            "result": _provider_result_payload(self.provider.get_technicals(stock)),
        }

    def get_fundamentals(self, symbol: str) -> dict[str, Any]:
        stock = self.resolver.resolve(symbol)
        return {
            "stock": stock.to_dict(),
            "result": _provider_result_payload(self.provider.get_fundamentals(stock)),
        }

    def get_news(self, symbol: str) -> dict[str, Any]:
        stock = self.resolver.resolve(symbol)
        return {
            "stock": stock.to_dict(),
            "result": _provider_result_payload(self.provider.get_news(stock)),
        }

    def get_capital_flow(self, symbol: str) -> dict[str, Any]:
        stock = self.resolver.resolve(symbol)
        if self.extras_provider is None:
            return {"stock": stock.to_dict(), "result": {"kind": "capital_flow", "source": "none", "ok": False, "data": {}, "error_message": "capital flow provider unavailable"}}
        return {"stock": stock.to_dict(), "result": _provider_result_payload(self.extras_provider.get_capital_flow(stock))}

    def get_longhubang(self, symbol: str) -> dict[str, Any]:
        stock = self.resolver.resolve(symbol)
        if self.extras_provider is None:
            return {"stock": stock.to_dict(), "result": {"kind": "longhubang", "source": "none", "ok": False, "data": {}, "error_message": "longhubang provider unavailable"}}
        return {"stock": stock.to_dict(), "result": _provider_result_payload(self.extras_provider.get_longhubang(stock))}

    def get_unlocks(self, symbol: str) -> dict[str, Any]:
        stock = self.resolver.resolve(symbol)
        if self.extras_provider is None:
            return {"stock": stock.to_dict(), "result": {"kind": "unlock", "source": "none", "ok": False, "data": {}, "error_message": "unlock provider unavailable"}}
        return {"stock": stock.to_dict(), "result": _provider_result_payload(self.extras_provider.get_unlocks(stock))}
