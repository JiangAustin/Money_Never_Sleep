"""Runtime A-share data providers for online analysis and tool-driven fallback."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable
from urllib import parse, request

from money_api.domains.analysis.contracts import StockIdentity
from money_api.domains.market_data.eastmoney_news import CompositeNewsProvider, EastmoneyNewsProvider
from money_api.domains.market_data.provider_results import ProviderResult
from money_api.domains.market_data.sina_kline import SinaKLineProvider
from money_api.domains.market_data.tencent_quote import TencentQuoteProvider
from money_api.domains.market_data.cls_market_flash import ClsMarketFlashProvider
from money_api.domains.market_data.sina_bulletin import SinaBulletinProvider


def _default_http_transport(url: str, timeout_s: float, headers: dict[str, str] | None = None) -> str:
    req = request.Request(url, headers=headers or {})
    with request.urlopen(req, timeout=timeout_s) as response:
        return response.read().decode("utf-8", errors="replace")


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        text = str(value).strip().replace(",", "").replace("%", "")
        if not text:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def _safe_str(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _normalize_f10_code(code: str) -> str:
    cleaned = _safe_str(code).upper()
    if cleaned.endswith((".SH", ".SZ", ".BJ")):
        return cleaned
    if cleaned.startswith(("6", "9")):
        return f"{cleaned}.SH"
    if cleaned.startswith(("0", "3")):
        return f"{cleaned}.SZ"
    if cleaned.startswith(("4", "8")):
        return f"{cleaned}.BJ"
    return f"{cleaned}.SZ"


def _first_row(payload: dict[str, Any]) -> dict[str, Any]:
    result = payload.get("result") or {}
    rows = result.get("data") or []
    if isinstance(rows, list) and rows:
        first = rows[0]
        if isinstance(first, dict):
            return first
    return {}


def _normalize_report_rows(payload: dict[str, Any], limit: int = 4) -> list[dict[str, Any]]:
    result = payload.get("result") or {}
    rows = result.get("data") or []
    normalized: list[dict[str, Any]] = []
    for item in rows[:limit]:
        if isinstance(item, dict):
            normalized.append(dict(item))
    return normalized


class EastmoneyTableProvider:
    """Fetch a thin Eastmoney report table and keep the raw rows visible."""

    def __init__(
        self,
        report_name: str,
        kind: str,
        columns: str,
        transport: Callable[[str], str] | None = None,
        timeout_s: float = 12.0,
        sort_columns: str = "REPORT_DATE",
        page_size: int = 10,
    ):
        self.report_name = report_name
        self.kind = kind
        self.columns = columns
        self.transport = transport
        self.timeout_s = timeout_s
        self.sort_columns = sort_columns
        self.page_size = page_size

    def _fetch_json(self, url: str) -> dict[str, Any]:
        headers = {
            "Host": "datacenter.eastmoney.com",
            "Origin": "https://emweb.securities.eastmoney.com",
            "Referer": "https://emweb.securities.eastmoney.com/",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
            ),
        }
        raw = self.transport(url) if self.transport is not None else _default_http_transport(url, self.timeout_s, headers=headers)
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
        raise ValueError("invalid eastmoney payload")

    def get_table(self, stock: StockIdentity) -> ProviderResult:
        fetched_at = datetime.now(timezone.utc).isoformat()
        url = (
            "https://datacenter.eastmoney.com/securities/api/data/v1/get?"
            + parse.urlencode(
                {
                    "reportName": self.report_name,
                    "columns": self.columns,
                    "quoteColumns": "",
                    "filter": f'(SECUCODE="{_normalize_f10_code(stock.code)}")',
                    "pageNumber": 1,
                    "pageSize": self.page_size,
                    "sortTypes": "-1",
                    "sortColumns": self.sort_columns,
                    "source": "HSF10",
                    "client": "PC",
                    "v": str(int(datetime.now(timezone.utc).timestamp())),
                }
            )
        )
        errors: list[str] = []
        try:
            payload = self._fetch_json(url)
            rows = _normalize_report_rows(payload, limit=self.page_size)
            data: dict[str, Any] = {
                "report_name": self.report_name,
                "rows": rows,
                "row_count": len(rows),
                "source_chain": [f"eastmoney:{self.report_name}"],
                "coverage": [self.kind] if rows else [],
            }
            if rows:
                data["summary"] = rows[0]
            return ProviderResult(
                kind=self.kind,
                source="eastmoney",
                ok=bool(rows),
                data=data if rows else {},
                error_type=None if rows else "RuntimeError",
                error_message=None if rows else f"{self.kind} unavailable",
                fetched_at=fetched_at,
            )
        except Exception as exc:
            errors.append(f"{type(exc).__name__}:{exc}")
            return ProviderResult(
                kind=self.kind,
                source="eastmoney",
                ok=False,
                data={},
                error_type=type(exc).__name__,
                error_message="; ".join(errors),
                fetched_at=fetched_at,
            )


class EastmoneyFundamentalsProvider:
    """Fetch compact fundamentals from Eastmoney F10 endpoints."""

    def __init__(self, transport: Callable[[str], str] | None = None, timeout_s: float = 12.0):
        self.transport = transport
        self.timeout_s = timeout_s

    def _fetch_json(self, url: str) -> dict[str, Any]:
        headers = {
            "Host": "datacenter.eastmoney.com",
            "Origin": "https://emweb.securities.eastmoney.com",
            "Referer": "https://emweb.securities.eastmoney.com/",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
            ),
        }
        raw = self.transport(url) if self.transport is not None else _default_http_transport(url, self.timeout_s, headers=headers)
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
        raise ValueError("invalid eastmoney payload")

    def _fetch_report(self, report_name: str, columns: str, stock_code: str, page_size: int = 10, sort_columns: str = "REPORT_DATE") -> dict[str, Any]:
        code = _normalize_f10_code(stock_code)
        url = (
            "https://datacenter.eastmoney.com/securities/api/data/v1/get?"
            + parse.urlencode(
                {
                    "reportName": report_name,
                    "columns": columns,
                    "quoteColumns": "",
                    "filter": f'(SECUCODE="{code}")',
                    "pageNumber": 1,
                    "pageSize": page_size,
                    "sortTypes": "-1",
                    "sortColumns": sort_columns,
                    "source": "HSF10",
                    "client": "PC",
                    "v": str(int(datetime.now(timezone.utc).timestamp())),
                }
            )
        )
        return self._fetch_json(url)

    def get_fundamentals(self, stock: StockIdentity) -> ProviderResult:
        fetched_at = datetime.now(timezone.utc).isoformat()
        errors: list[str] = []
        data: dict[str, Any] = {
            "coverage": [],
            "source_chain": [],
            "as_of": fetched_at,
        }

        try:
            latest = self._fetch_report(
                "RPT_PCF10_FINANCEMAINFINADATA",
                "SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,REPORT_DATE,REPORT_TYPE,EPSJB,EPSKCJB,EPSXS,BPS,MGZBGJ,MGWFPLR,MGJYXJJE,TOTAL_OPERATEINCOME,TOTAL_OPERATEINCOME_LAST,PARENT_NETPROFIT,PARENT_NETPROFIT_LAST,KCFJCXSYJLR,KCFJCXSYJLR_LAST,ROEJQ,ROEJQ_LAST,XSMLL,XSMLL_LAST,ZCFZL,ZCFZL_LAST,YYZSRGDHBZC_LAST,YYZSRGDHBZC,NETPROFITRPHBZC,NETPROFITRPHBZC_LAST,KFJLRGDHBZC,KFJLRGDHBZC_LAST,TOTALOPERATEREVETZ,TOTALOPERATEREVETZ_LAST,PARENTNETPROFITTZ,PARENTNETPROFITTZ_LAST,KCFJCXSYJYLRTZ,KCFJCXSYJYLRTZ_LAST,TOTAL_SHARE,FREE_SHARE,EPSJB_PL,BPS_PL,FORMERNAME",
                stock.code,
                page_size=1,
            )
            latest_row = _first_row(latest)
            if latest_row:
                data["latest_finance"] = {
                    "report_date": latest_row.get("REPORT_DATE"),
                    "report_type": latest_row.get("REPORT_TYPE"),
                    "eps": _safe_float(latest_row.get("EPSJB")),
                    "eps_basic": _safe_float(latest_row.get("EPSKCJB")),
                    "bps": _safe_float(latest_row.get("BPS")),
                    "revenue": _safe_float(latest_row.get("TOTAL_OPERATEINCOME")),
                    "revenue_prev": _safe_float(latest_row.get("TOTAL_OPERATEINCOME_LAST")),
                    "revenue_yoy": _safe_float(latest_row.get("TOTALOPERATEREVETZ")),
                    "net_profit": _safe_float(latest_row.get("PARENT_NETPROFIT")),
                    "net_profit_prev": _safe_float(latest_row.get("PARENT_NETPROFIT_LAST")),
                    "net_profit_yoy": _safe_float(latest_row.get("PARENTNETPROFITTZ")),
                    "net_profit_ex_non": _safe_float(latest_row.get("KCFJCXSYJLR")),
                    "roe": _safe_float(latest_row.get("ROEJQ")),
                    "gross_margin": _safe_float(latest_row.get("XSMLL")),
                    "asset_liability_ratio": _safe_float(latest_row.get("ZCFZL")),
                    "shares_total": _safe_float(latest_row.get("TOTAL_SHARE")),
                    "shares_float": _safe_float(latest_row.get("FREE_SHARE")),
                }
                data["coverage"].append("latest_finance")
                data["source_chain"].append("eastmoney:RPT_PCF10_FINANCEMAINFINADATA")
        except Exception as exc:
            errors.append(f"latest_finance:{type(exc).__name__}:{exc}")

        try:
            quarterly = self._fetch_report(
                "RPT_F10_QTR_MAINFINADATA",
                "SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,ORG_CODE,REPORT_DATE,EPSJB,BPS,PER_CAPITAL_RESERVE,PER_UNASSIGN_PROFIT,PER_NETCASH,TOTALOPERATEREVE,GROSS_PROFIT,PARENTNETPROFIT,DEDU_PARENT_PROFIT,TOTALOPERATEREVETZ,PARENTNETPROFITTZ,DPNP_YOY_RATIO,YYZSRGDHBZC,NETPROFITRPHBZC,KFJLRGDHBZC,ROE_DILUTED,JROA,NET_PROFIT_RATIO,GROSS_PROFIT_RATIO",
                stock.code,
                page_size=4,
            )
            rows = _normalize_report_rows(quarterly, limit=4)
            if rows:
                data["quarterly_finance"] = [
                    {
                        "report_date": row.get("REPORT_DATE"),
                        "eps": _safe_float(row.get("EPSJB")),
                        "bps": _safe_float(row.get("BPS")),
                        "revenue": _safe_float(row.get("TOTALOPERATEREVE")),
                        "net_profit": _safe_float(row.get("PARENTNETPROFIT")),
                        "revenue_yoy": _safe_float(row.get("TOTALOPERATEREVETZ")),
                        "net_profit_yoy": _safe_float(row.get("PARENTNETPROFITTZ")),
                        "roe": _safe_float(row.get("ROE_DILUTED")),
                        "gross_margin": _safe_float(row.get("GROSS_PROFIT_RATIO")),
                    }
                    for row in rows
                ]
                data["coverage"].append("quarterly_finance")
                data["source_chain"].append("eastmoney:RPT_F10_QTR_MAINFINADATA")
        except Exception as exc:
            errors.append(f"quarterly_finance:{type(exc).__name__}:{exc}")

        try:
            predict_summary = self._fetch_report(
                "RPT_HSF10_RESPREDICT_STATISTICS",
                "SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,YEAR,YEAR_MARK,EPS,EPS_RATIO,PE",
                stock.code,
                page_size=6,
                sort_columns="RANK",
            )
            rows = _normalize_report_rows(predict_summary, limit=6)
            if rows:
                data["predict_summary"] = [
                    {
                        "year": row.get("YEAR"),
                        "year_mark": row.get("YEAR_MARK"),
                        "eps": _safe_float(row.get("EPS")),
                        "eps_ratio": _safe_float(row.get("EPS_RATIO")),
                        "pe": _safe_float(row.get("PE")),
                    }
                    for row in rows
                ]
                data["coverage"].append("predict_summary")
                data["source_chain"].append("eastmoney:RPT_HSF10_RESPREDICT_STATISTICS")
        except Exception as exc:
            errors.append(f"predict_summary:{type(exc).__name__}:{exc}")

        try:
            valuation = self._fetch_report(
                "RPT_STOCKVALUATIONTANTILE",
                "SECUCODE,STATISTICS_CYCLE,INDEX_TYPE,PERCENTILE_THIRTY,PERCENTILE_FIFTY,PERCENTILE_SEVENTY",
                stock.code,
                page_size=1,
                sort_columns="",
            )
            row = _first_row(valuation)
            if row:
                data["valuation_percentile"] = {
                    "statistics_cycle": row.get("STATISTICS_CYCLE"),
                    "index_type": row.get("INDEX_TYPE"),
                    "percentile_30": _safe_float(row.get("PERCENTILE_THIRTY")),
                    "percentile_50": _safe_float(row.get("PERCENTILE_FIFTY")),
                    "percentile_70": _safe_float(row.get("PERCENTILE_SEVENTY")),
                }
                data["coverage"].append("valuation_percentile")
                data["source_chain"].append("eastmoney:RPT_STOCKVALUATIONTANTILE")
        except Exception as exc:
            errors.append(f"valuation_percentile:{type(exc).__name__}:{exc}")

        try:
            margin = self._fetch_report(
                "RPT_MARGIN_STATISTICS_STOCKS",
                "SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,TRADE_DATE,FIN_BUY_AMT,FIN_REPAY_AMT,FIN_BALANCE,LOAN_SELL_VOL,LOAN_REPAY_VOL,LOAN_BALANCE",
                stock.code,
                page_size=3,
            )
            rows = _normalize_report_rows(margin, limit=3)
            if rows:
                data["margin_trading"] = [
                    {
                        "trade_date": row.get("TRADE_DATE"),
                        "fin_buy_amt": _safe_float(row.get("FIN_BUY_AMT")),
                        "fin_repay_amt": _safe_float(row.get("FIN_REPAY_AMT")),
                        "fin_balance": _safe_float(row.get("FIN_BALANCE")),
                        "loan_sell_vol": _safe_float(row.get("LOAN_SELL_VOL")),
                        "loan_repay_vol": _safe_float(row.get("LOAN_REPAY_VOL")),
                        "loan_balance": _safe_float(row.get("LOAN_BALANCE")),
                    }
                    for row in rows
                ]
                data["coverage"].append("margin_trading")
                data["source_chain"].append("eastmoney:RPT_MARGIN_STATISTICS_STOCKS")
        except Exception as exc:
            errors.append(f"margin_trading:{type(exc).__name__}:{exc}")

        ok = bool(data.get("coverage"))
        return ProviderResult(
            kind="fundamentals",
            source="eastmoney",
            ok=ok,
            data=data if ok else {},
            error_type=None if ok else "RuntimeError",
            error_message=None if ok else "; ".join(errors) or "eastmoney fundamentals unavailable",
            fetched_at=fetched_at,
        )


class IwencaiFundamentalsProvider:
    """Fetch fundamentals or search snapshots from iWenCai when API key is configured."""

    def __init__(
        self,
        api_key: str | None = None,
        transport: Callable[[str], str] | None = None,
        timeout_s: float = 20.0,
        query_template: str = "{name} 财务指标 基本面",
    ):
        self.api_key = (api_key or os.getenv("MONEY_IWENCAI_API_KEY", "")).strip()
        self.transport = transport
        self.timeout_s = timeout_s
        self.query_template = query_template

    def _post_json(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if self.transport is not None:
            # Keep transport intentionally simple: tests can inject a one-arg transport that returns JSON.
            parsed = json.loads(self.transport(url))
        else:
            req = request.Request(url, data=raw, headers=headers, method="POST")
            with request.urlopen(req, timeout=self.timeout_s) as response:
                parsed = json.loads(response.read().decode("utf-8", errors="replace"))
        if isinstance(parsed, dict):
            return parsed
        raise ValueError("invalid iwencai payload")

    def get_fundamentals(self, stock: StockIdentity) -> ProviderResult:
        fetched_at = datetime.now(timezone.utc).isoformat()
        if not self.api_key:
            return ProviderResult(
                kind="fundamentals",
                source="iwencai",
                ok=False,
                data={},
                error_type="ConfigurationError",
                error_message="同花顺问财 API 密钥未配置",
                fetched_at=fetched_at,
            )

        query = self.query_template.format(code=stock.code, name=stock.name)
        payload = {
            "query": query,
            "page": "1",
            "limit": "5",
            "is_cache": "1",
            "expand_index": "true",
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Claw-Call-Type": "normal",
            "X-Claw-Skill-Id": "query2data",
            "X-Claw-Skill-Version": "1.0.0",
            "X-Claw-Plugin-Id": "none",
            "X-Claw-Plugin-Version": "none",
            "X-Claw-Trace-Id": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f"),
        }

        try:
            result = self._post_json("https://openapi.iwencai.com/v1/query2data", payload, headers)
            if int(result.get("status_code", 0)) != 0:
                raise ValueError(str(result.get("status_msg") or "iwencai query failed"))
            datas = result.get("datas") or []
            rows = [dict(item) for item in datas[:5] if isinstance(item, dict)]
            data = {
                "query": query,
                "code_count": result.get("code_count", len(rows)),
                "rows": rows,
                "chunks_info": result.get("chunks_info"),
            }
            return ProviderResult(
                kind="fundamentals",
                source="iwencai",
                ok=bool(rows),
                data=data,
                fetched_at=fetched_at,
            )
        except Exception as exc:
            return ProviderResult(
                kind="fundamentals",
                source="iwencai",
                ok=False,
                data={},
                error_type=type(exc).__name__,
                error_message=str(exc),
                fetched_at=fetched_at,
            )


class CompositeFundamentalsProvider:
    def __init__(self, providers: list[object]):
        self.providers = providers

    def get_fundamentals(self, stock: StockIdentity) -> ProviderResult:
        merged: dict[str, Any] = {
            "coverage": [],
            "source_chain": [],
            "providers": [],
        }
        errors: list[str] = []
        ok = False
        fetched_at = datetime.now(timezone.utc).isoformat()
        sources: list[str] = []

        for provider in self.providers:
            result = provider.get_fundamentals(stock)
            if result.source not in sources:
                sources.append(result.source)
            merged["providers"].append({"source": result.source, "ok": result.ok})
            if result.ok and isinstance(result.data, dict):
                ok = True
                merged.update(result.data)
            if isinstance(result.data, dict):
                for key in ("coverage", "source_chain"):
                    if isinstance(result.data.get(key), list):
                        for item in result.data[key]:
                            if item not in merged[key]:
                                merged[key].append(item)
            if result.error_message:
                errors.append(f"{result.source}: {result.error_message}")

        return ProviderResult(
            kind="fundamentals",
            source="+".join(sources) if sources else "none",
            ok=ok,
            data=merged if ok else {},
            error_type=None if ok else "RuntimeError",
            error_message=None if ok else "; ".join(errors) or "all fundamentals providers failed",
            fetched_at=fetched_at,
        )


@dataclass
class SinaTechnicalsProvider:
    """Derive a compact technical snapshot from Sina daily K-line data."""

    price_provider: SinaKLineProvider
    lookback: int = 60

    def get_technicals(self, stock: StockIdentity) -> ProviderResult:
        fetched_at = datetime.now(timezone.utc).isoformat()
        series_result = self.price_provider.get_price_series(stock, limit=self.lookback)
        if not series_result.ok or not isinstance(series_result.data, list) or not series_result.data:
            return ProviderResult(
                kind="technicals",
                source="sina",
                ok=False,
                data={},
                error_type=series_result.error_type or "RuntimeError",
                error_message=series_result.error_message or "Sina K-line unavailable",
                fetched_at=fetched_at,
            )

        closes = [float(point.close) for point in series_result.data if getattr(point, "close", 0) > 0]
        if not closes:
            return ProviderResult(
                kind="technicals",
                source="sina",
                ok=False,
                data={},
                error_type="ValueError",
                error_message="K-line series has no valid close prices",
                fetched_at=fetched_at,
            )

        def _moving_average(window: int) -> float | None:
            if len(closes) < window:
                return None
            sample = closes[-window:]
            return round(sum(sample) / window, 4)

        latest_close = round(closes[-1], 4)
        change_5d = None
        change_20d = None
        if len(closes) > 5 and closes[-6] > 0:
            change_5d = round((latest_close / closes[-6] - 1) * 100, 4)
        if len(closes) > 20 and closes[-21] > 0:
            change_20d = round((latest_close / closes[-21] - 1) * 100, 4)

        data = {
            "series_source": series_result.source,
            "latest_close": latest_close,
            "ma5": _moving_average(5),
            "ma10": _moving_average(10),
            "ma20": _moving_average(20),
            "ma60": _moving_average(60),
            "change_5d_pct": change_5d,
            "change_20d_pct": change_20d,
            "sample_size": len(closes),
            "as_of": fetched_at,
        }
        return ProviderResult(kind="technicals", source="sina", ok=True, data=data, fetched_at=fetched_at)


@dataclass
class RuntimeAshareMarketDataProvider:
    quote_provider: TencentQuoteProvider
    technicals_provider: SinaTechnicalsProvider
    fundamentals_provider: CompositeFundamentalsProvider
    news_provider: CompositeNewsProvider

    def get_quote(self, stock: StockIdentity) -> ProviderResult:
        return self.quote_provider.get_quote(stock)

    def get_technicals(self, stock: StockIdentity) -> ProviderResult:
        return self.technicals_provider.get_technicals(stock)

    def get_fundamentals(self, stock: StockIdentity) -> ProviderResult:
        return self.fundamentals_provider.get_fundamentals(stock)

    def get_news(self, stock: StockIdentity) -> ProviderResult:
        return self.news_provider.get_news(stock)


@dataclass
class RuntimeAshareResearchExtrasProvider:
    capital_flow_provider: EastmoneyTableProvider
    longhubang_provider: EastmoneyTableProvider
    unlock_provider: EastmoneyTableProvider

    def get_capital_flow(self, stock: StockIdentity) -> ProviderResult:
        return self.capital_flow_provider.get_table(stock)

    def get_longhubang(self, stock: StockIdentity) -> ProviderResult:
        return self.longhubang_provider.get_table(stock)

    def get_unlocks(self, stock: StockIdentity) -> ProviderResult:
        return self.unlock_provider.get_table(stock)


def build_runtime_ashare_market_data_provider(
    quote_transport: Callable[[str], str] | None = None,
    news_transport: Callable[[str], str] | None = None,
    flash_transport: Callable[[str], dict[str, object]] | None = None,
    bulletin_transport: Callable[[str], str] | None = None,
    kline_transport: Callable[[str], str] | None = None,
    eastmoney_transport: Callable[[str], str] | None = None,
    iwencai_api_key: str | None = None,
    iwencai_transport: Callable[[str], str] | None = None,
) -> RuntimeAshareMarketDataProvider:
    news_provider = CompositeNewsProvider(
        [
            EastmoneyNewsProvider(transport=news_transport),
            ClsMarketFlashProvider(transport=flash_transport),
            SinaBulletinProvider(transport=bulletin_transport),
        ]
    )
    fundamentals_provider = CompositeFundamentalsProvider(
        [
            EastmoneyFundamentalsProvider(transport=eastmoney_transport),
            IwencaiFundamentalsProvider(api_key=iwencai_api_key, transport=iwencai_transport),
        ]
    )
    return RuntimeAshareMarketDataProvider(
        quote_provider=TencentQuoteProvider(transport=quote_transport),
        technicals_provider=SinaTechnicalsProvider(price_provider=SinaKLineProvider(transport=kline_transport)),
        fundamentals_provider=fundamentals_provider,
        news_provider=news_provider,
    )


def build_runtime_ashare_research_extras_provider(
    eastmoney_transport: Callable[[str], str] | None = None,
) -> RuntimeAshareResearchExtrasProvider:
    return RuntimeAshareResearchExtrasProvider(
        capital_flow_provider=EastmoneyTableProvider(
            report_name="RPT_STOCK_MAINFUND_FLOW",
            kind="capital_flow",
            columns="SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,TRADE_DATE,MAIN_NET_INFLOW,MAIN_NET_INFLOW_RATE,MAIN_BUY,MAIN_SELL",
            transport=eastmoney_transport,
            page_size=5,
        ),
        longhubang_provider=EastmoneyTableProvider(
            report_name="RPT_DAILYBILLBOARD_DETAILS",
            kind="longhubang",
            columns="SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,TRADE_DATE,BUY_AMT,SELL_AMT,NET_AMT,ORGAN_AMT",
            transport=eastmoney_transport,
            page_size=5,
        ),
        unlock_provider=EastmoneyTableProvider(
            report_name="RPT_STOCK_LIFTING_SCHEDULE",
            kind="unlock",
            columns="SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,UNLOCK_DATE,UNLOCK_NUM,UNLOCK_VALUE,UNLOCK_RATIO",
            transport=eastmoney_transport,
            page_size=5,
        ),
    )
