"""Version 1 route functions for the Money_Never_sleep API."""

from collections.abc import Callable
import os

from money_api.core.config import settings
from money_api.domains.analysis.agent_engine import MockDeepResearchEngine, QuickAgentRouter
from money_api.domains.analysis.context_builder import DataContextBuilder, StaticMarketDataProvider
from money_api.domains.analysis.contracts import BacktestOptions, BacktestPricePoint
from money_api.domains.analysis.research_tools import ResearchToolService
from money_api.domains.analysis.report_repository import AnalysisReportRepository, JsonFileAnalysisReportRepository
from money_api.domains.analysis.service import AnalysisService
from money_api.domains.analysis.tradingagents_engine import (
    AutoFallbackDeepResearchEngine,
    FakeTradingAgentsRunner,
    TradingAgentsDeepResearchEngine,
    TradingAgentsRunner,
)
from money_api.domains.analysis.tool_driven_engine import ToolDrivenResearchEngine
from money_api.integrations.tradingagents_runner import TradingAgentsGraphRunner
from money_api.domains.market_data.ashare_runtime import build_runtime_ashare_market_data_provider, build_runtime_ashare_research_extras_provider
from money_api.domains.market_data.resolver import StockResolver
from money_api.domains.market_data.sina_kline import SinaKLineProvider


def _build_static_market_data_provider() -> StaticMarketDataProvider:
    return StaticMarketDataProvider(
        quote={"price": 1688.0},
        technicals={"ma5": 1660.0, "ma10": 1625.0, "ma20": 1588.0},
        fundamentals={"pe_ttm": 28.5, "pb": 9.1},
        news=[{"title": "示例公司发布2026年半年度业绩预告", "content": "业绩保持稳定", "source": "static"}],
    )


def _build_stock_resolver() -> StockResolver:
    return StockResolver(name_map={"贵州茅台": "600519", "平安银行": "000001"})


def build_default_analysis_service(report_repository: AnalysisReportRepository | None = None) -> AnalysisService:
    return AnalysisService(
        resolver=_build_stock_resolver(),
        context_builder=DataContextBuilder(_build_static_market_data_provider()),
        quick_router=QuickAgentRouter(),
        deep_engine=MockDeepResearchEngine(),
        report_repository=report_repository or JsonFileAnalysisReportRepository(settings.analysis_reports_dir),
    )


def build_tencent_quote_analysis_service(
    transport: Callable[[str], str] | None = None,
    news_transport: Callable[[str], str] | None = None,
    flash_transport: Callable[[str], dict[str, object]] | None = None,
    bulletin_transport: Callable[[str], str] | None = None,
    kline_transport: Callable[[str], str] | None = None,
    eastmoney_transport: Callable[[str], str] | None = None,
    iwencai_api_key: str | None = None,
    iwencai_transport: Callable[[str], str] | None = None,
    report_repository: AnalysisReportRepository | None = None,
) -> AnalysisService:
    provider = build_runtime_ashare_market_data_provider(
        quote_transport=transport,
        news_transport=news_transport,
        flash_transport=flash_transport,
        bulletin_transport=bulletin_transport,
        kline_transport=kline_transport,
        eastmoney_transport=eastmoney_transport,
        iwencai_api_key=iwencai_api_key,
        iwencai_transport=iwencai_transport,
    )
    return AnalysisService(
        resolver=_build_stock_resolver(),
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
        resolver=_build_stock_resolver(),
        context_builder=DataContextBuilder(_build_static_market_data_provider()),
        quick_router=QuickAgentRouter(),
        deep_engine=TradingAgentsDeepResearchEngine(runner or FakeTradingAgentsRunner()),
        report_repository=report_repository,
    )


def build_runtime_analysis_service(
    transport: Callable[[str], str] | None = None,
    news_transport: Callable[[str], str] | None = None,
    flash_transport: Callable[[str], dict[str, object]] | None = None,
    bulletin_transport: Callable[[str], str] | None = None,
    kline_transport: Callable[[str], str] | None = None,
    eastmoney_transport: Callable[[str], str] | None = None,
    iwencai_api_key: str | None = None,
    iwencai_transport: Callable[[str], str] | None = None,
    report_repository: AnalysisReportRepository | None = None,
    tradingagents_runner: TradingAgentsRunner | None = None,
) -> AnalysisService:
    market_data_mode = os.getenv("MONEY_MARKET_DATA_MODE", "tencent").lower()
    deep_engine_mode = os.getenv("MONEY_DEEP_ENGINE", "auto").lower()

    provider = _build_static_market_data_provider()
    if market_data_mode in {"tencent", "online"}:
        provider = build_runtime_ashare_market_data_provider(
            quote_transport=transport,
            news_transport=news_transport,
            flash_transport=flash_transport,
            bulletin_transport=bulletin_transport,
            kline_transport=kline_transport,
            eastmoney_transport=eastmoney_transport,
            iwencai_api_key=iwencai_api_key,
            iwencai_transport=iwencai_transport,
        )

    deep_engine = MockDeepResearchEngine()
    if deep_engine_mode == "tradingagents":
        deep_engine = TradingAgentsDeepResearchEngine(tradingagents_runner or TradingAgentsGraphRunner())
    elif deep_engine_mode == "auto":
        deep_engine = AutoFallbackDeepResearchEngine(
            primary=TradingAgentsDeepResearchEngine(tradingagents_runner or TradingAgentsGraphRunner()),
            fallback=ToolDrivenResearchEngine(),
        )

    return AnalysisService(
        resolver=_build_stock_resolver(),
        context_builder=DataContextBuilder(provider),
        quick_router=QuickAgentRouter(),
        deep_engine=deep_engine,
        report_repository=report_repository or JsonFileAnalysisReportRepository(settings.analysis_reports_dir),
    )


def build_default_research_tool_service() -> ResearchToolService:
    provider = _build_static_market_data_provider()
    return ResearchToolService(resolver=_build_stock_resolver(), provider=provider)


def build_runtime_research_tool_service(
    quote_transport: Callable[[str], str] | None = None,
    news_transport: Callable[[str], str] | None = None,
    flash_transport: Callable[[str], dict[str, object]] | None = None,
    bulletin_transport: Callable[[str], str] | None = None,
    kline_transport: Callable[[str], str] | None = None,
    eastmoney_transport: Callable[[str], str] | None = None,
    iwencai_api_key: str | None = None,
    iwencai_transport: Callable[[str], str] | None = None,
) -> ResearchToolService:
    provider = build_runtime_ashare_market_data_provider(
        quote_transport=quote_transport,
        news_transport=news_transport,
        flash_transport=flash_transport,
        bulletin_transport=bulletin_transport,
        kline_transport=kline_transport,
        eastmoney_transport=eastmoney_transport,
        iwencai_api_key=iwencai_api_key,
        iwencai_transport=iwencai_transport,
    )
    extras_provider = build_runtime_ashare_research_extras_provider(eastmoney_transport=eastmoney_transport)
    return ResearchToolService(resolver=_build_stock_resolver(), provider=provider, extras_provider=extras_provider)


_analysis_service = build_default_analysis_service()
_research_tool_service = build_default_research_tool_service()


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


def get_research_context(symbol: str) -> dict[str, object]:
    return _research_tool_service.build_context(symbol).to_dict()


def get_research_quote(symbol: str) -> dict[str, object]:
    return _research_tool_service.get_quote(symbol)


def get_research_technicals(symbol: str) -> dict[str, object]:
    return _research_tool_service.get_technicals(symbol)


def get_research_fundamentals(symbol: str) -> dict[str, object]:
    return _research_tool_service.get_fundamentals(symbol)


def get_research_news(symbol: str) -> dict[str, object]:
    return _research_tool_service.get_news(symbol)


def get_research_capital_flow(symbol: str) -> dict[str, object]:
    return _research_tool_service.get_capital_flow(symbol)


def get_research_longhubang(symbol: str) -> dict[str, object]:
    return _research_tool_service.get_longhubang(symbol)


def get_research_unlocks(symbol: str) -> dict[str, object]:
    return _research_tool_service.get_unlocks(symbol)


def routes() -> dict[str, object]:
    """Return an early scaffold snapshot of v1 route payloads.

    This is not a web-framework route table. It preserves the original scaffold
    behavior by returning the current health payload until a real API router is
    introduced.
    """
    from money_api.main import health

    return {"health": health()}
