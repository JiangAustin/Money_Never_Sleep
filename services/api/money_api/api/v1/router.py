"""Version 1 route functions for the Money_Never_sleep API."""

from collections.abc import Callable
import os

from money_api.core.config import settings
from money_api.domains.analysis.agent_engine import MockDeepResearchEngine, QuickAgentRouter
from money_api.domains.analysis.context_builder import DataContextBuilder, StaticMarketDataProvider
from money_api.domains.analysis.contracts import BacktestOptions, BacktestPricePoint, StockIdentity
from money_api.domains.analysis.report_repository import AnalysisReportRepository, JsonFileAnalysisReportRepository
from money_api.domains.analysis.service import AnalysisService
from money_api.domains.analysis.tradingagents_engine import (
    AutoFallbackDeepResearchEngine,
    FakeTradingAgentsRunner,
    TradingAgentsDeepResearchEngine,
    TradingAgentsRunner,
)
from money_api.domains.market_data.provider_results import ProviderResult
from money_api.domains.market_data.eastmoney_news import EastmoneyNewsProvider
from money_api.domains.market_data.resolver import StockResolver
from money_api.domains.market_data.sina_kline import SinaKLineProvider
from money_api.domains.market_data.tencent_quote import TencentQuoteProvider


class QuoteOverrideProvider:
    """Compose Tencent quote with static offline payloads for other data kinds."""

    def __init__(
        self,
        quote_provider: TencentQuoteProvider,
        fallback: StaticMarketDataProvider,
        news_provider: EastmoneyNewsProvider | None = None,
    ):
        self.quote_provider = quote_provider
        self.fallback = fallback
        self.news_provider = news_provider

    def get_quote(self, stock: StockIdentity) -> ProviderResult:
        return self.quote_provider.get_quote(stock)

    def get_technicals(self, stock: StockIdentity) -> ProviderResult:
        return self.fallback.get_technicals(stock)

    def get_fundamentals(self, stock: StockIdentity) -> ProviderResult:
        return self.fallback.get_fundamentals(stock)

    def get_news(self, stock: StockIdentity) -> ProviderResult:
        if self.news_provider is not None:
            return self.news_provider.get_news(stock)
        return self.fallback.get_news(stock)


def build_default_analysis_service(report_repository: AnalysisReportRepository | None = None) -> AnalysisService:
    return AnalysisService(
        resolver=StockResolver(name_map={"贵州茅台": "600519", "平安银行": "000001"}),
        context_builder=DataContextBuilder(
            StaticMarketDataProvider(
                quote={"price": 1688.0},
                technicals={"ma5": 1660.0, "ma10": 1625.0, "ma20": 1588.0},
                fundamentals={"pe_ttm": 28.5, "pb": 9.1},
                news=[{"title": "示例新闻：业绩保持稳定"}],
            )
        ),
        quick_router=QuickAgentRouter(),
        deep_engine=MockDeepResearchEngine(),
        report_repository=report_repository or JsonFileAnalysisReportRepository(settings.analysis_reports_dir),
    )


def build_tencent_quote_analysis_service(
    transport: Callable[[str], str] | None = None,
    news_transport: Callable[[str], str] | None = None,
    report_repository: AnalysisReportRepository | None = None,
) -> AnalysisService:
    fallback_provider = StaticMarketDataProvider(
        technicals={"ma5": 1660.0, "ma10": 1625.0, "ma20": 1588.0},
        fundamentals={"pe_ttm": 28.5, "pb": 9.1},
        news=[{"title": "示例新闻：业绩保持稳定"}],
    )
    provider = QuoteOverrideProvider(
        quote_provider=TencentQuoteProvider(transport=transport),
        fallback=fallback_provider,
        news_provider=EastmoneyNewsProvider(transport=news_transport),
    )
    return AnalysisService(
        resolver=StockResolver(name_map={"贵州茅台": "600519", "平安银行": "000001"}),
        context_builder=DataContextBuilder(provider),
        quick_router=QuickAgentRouter(),
        deep_engine=MockDeepResearchEngine(),
        report_repository=report_repository,
    )


def build_tradingagents_analysis_service(
    runner: TradingAgentsRunner | None = None,
    report_repository: AnalysisReportRepository | None = None,
) -> AnalysisService:
    return AnalysisService(
        resolver=StockResolver(name_map={"贵州茅台": "600519", "平安银行": "000001"}),
        context_builder=DataContextBuilder(
            StaticMarketDataProvider(
                quote={"price": 1688.0},
                technicals={"ma5": 1660.0, "ma10": 1625.0, "ma20": 1588.0},
                fundamentals={"pe_ttm": 28.5, "pb": 9.1},
                news=[{"title": "示例新闻：业绩保持稳定"}],
            )
        ),
        quick_router=QuickAgentRouter(),
        deep_engine=TradingAgentsDeepResearchEngine(runner or FakeTradingAgentsRunner()),
        report_repository=report_repository,
    )


def build_runtime_analysis_service(
    transport: Callable[[str], str] | None = None,
    news_transport: Callable[[str], str] | None = None,
    report_repository: AnalysisReportRepository | None = None,
    tradingagents_runner: TradingAgentsRunner | None = None,
) -> AnalysisService:
    market_data_mode = os.getenv("MONEY_MARKET_DATA_MODE", "tencent").lower()
    deep_engine_mode = os.getenv("MONEY_DEEP_ENGINE", "auto").lower()

    static_provider = StaticMarketDataProvider(
        quote={"price": 1688.0},
        technicals={"ma5": 1660.0, "ma10": 1625.0, "ma20": 1588.0},
        fundamentals={"pe_ttm": 28.5, "pb": 9.1},
        news=[{"title": "示例新闻：业绩保持稳定"}],
    )
    provider = static_provider
    if market_data_mode == "tencent":
        provider = QuoteOverrideProvider(
            quote_provider=TencentQuoteProvider(transport=transport),
            fallback=StaticMarketDataProvider(
                technicals={"ma5": 1660.0, "ma10": 1625.0, "ma20": 1588.0},
                fundamentals={"pe_ttm": 28.5, "pb": 9.1},
                news=[{"title": "示例新闻：业绩保持稳定"}],
            ),
            news_provider=EastmoneyNewsProvider(transport=news_transport),
        )

    deep_engine = MockDeepResearchEngine()
    if deep_engine_mode == "tradingagents":
        deep_engine = TradingAgentsDeepResearchEngine(tradingagents_runner or TradingAgentsGraphRunner())
    elif deep_engine_mode == "auto":
        deep_engine = AutoFallbackDeepResearchEngine(
            primary=TradingAgentsDeepResearchEngine(tradingagents_runner or TradingAgentsGraphRunner()),
            fallback=MockDeepResearchEngine(),
        )

    return AnalysisService(
        resolver=StockResolver(name_map={"贵州茅台": "600519", "平安银行": "000001"}),
        context_builder=DataContextBuilder(provider),
        quick_router=QuickAgentRouter(),
        deep_engine=deep_engine,
        report_repository=report_repository or JsonFileAnalysisReportRepository(settings.analysis_reports_dir),
    )


_analysis_service = build_default_analysis_service()


def analyze_stock(symbol: str, message: str) -> dict[str, object]:
    return _analysis_service.create_single_stock_analysis(symbol, message).to_dict()


def get_analysis_report(task_id: str) -> dict[str, object] | None:
    report = _analysis_service.get_report(task_id)
    return report.to_dict() if report is not None else None


def list_analysis_reports(limit: int = 20) -> list[dict[str, object]]:
    return [record.to_dict() for record in _analysis_service.list_reports(limit=limit)]


def backtest_analysis_report(
    task_id: str,
    prices: list[dict[str, object]] | None = None,
    source: str | None = None,
    limit: int = 60,
    options: dict[str, object] | None = None,
) -> dict[str, object] | None:
    backtest_options = BacktestOptions.from_dict(options)
    if source == "sina":
        result = _analysis_service.backtest_report_from_provider(task_id, SinaKLineProvider(), limit=limit, options=backtest_options)
    else:
        price_points = [BacktestPricePoint.from_dict(price) for price in (prices or [])]
        result = _analysis_service.backtest_report(task_id, price_points, options=backtest_options)
    return result.to_dict() if result is not None else None


def build_portfolio_risk_budget(task_ids: list[str] | None = None, limit: int = 20) -> dict[str, object]:
    return _analysis_service.build_portfolio_risk_budget(task_ids=task_ids, limit=limit).to_dict()


def routes() -> dict[str, object]:
    """Return an early scaffold snapshot of v1 route payloads.

    This is not a web-framework route table. It preserves the original scaffold
    behavior by returning the current health payload until a real API router is
    introduced.
    """
    from money_api.main import health

    return {"health": health()}
