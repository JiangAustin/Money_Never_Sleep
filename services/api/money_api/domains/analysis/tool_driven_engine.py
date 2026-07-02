"""Deterministic deep-research fallback powered by real online tool outputs."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from money_api.domains.analysis.contracts import (
    AgentView,
    AnalysisReport,
    AnalysisStatus,
    ConfidenceLevel,
    DataContext,
    DecisionAction,
    RiskFinding,
)
from money_api.domains.analysis.provenance import collect_data_sources


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _summarize_event_signal(events: list[Any]) -> dict[str, int]:
    positive_types = {"earnings_forecast", "share_repurchase", "share_increase"}
    negative_types = {"share_reduction", "guarantee", "share_pledge"}
    high_priority = [event for event in events if getattr(event, "priority", "medium") == "high"]
    return {
        "positive": sum(1 for event in high_priority if getattr(event, "event_type", None) and getattr(event.event_type, "value", event.event_type) in positive_types),
        "negative": sum(1 for event in high_priority if getattr(event, "event_type", None) and getattr(event.event_type, "value", event.event_type) in negative_types),
    }


def _maybe_append(texts: list[str], text: str | None) -> None:
    if text and text not in texts:
        texts.append(text)


class ToolDrivenResearchEngine:
    """Generate a usable report from the live data context without LLM access."""

    def analyze(self, task_id: str, context: DataContext) -> AnalysisReport:
        quote = context.quote or {}
        technicals = context.technicals or {}
        fundamentals = context.fundamentals or {}
        news_items = context.news or []
        events = list(context.events or [])
        data_sources = collect_data_sources(context.diagnostics)

        price = _safe_float(quote.get("price"))
        change_pct = _safe_float(quote.get("change_pct"))
        pe_ttm = _safe_float(quote.get("pe_ttm"))
        pb = _safe_float(quote.get("pb"))
        ma5 = _safe_float(technicals.get("ma5"))
        ma20 = _safe_float(technicals.get("ma20"))
        latest_close = _safe_float(technicals.get("latest_close")) or price

        latest_finance = fundamentals.get("latest_finance") or {}
        quarterly = fundamentals.get("quarterly_finance") or []
        valuation = fundamentals.get("valuation_percentile") or {}
        predict_summary = fundamentals.get("predict_summary") or []
        iwencai_rows = (fundamentals.get("iwencai") or {}).get("rows") if isinstance(fundamentals.get("iwencai"), dict) else []

        revenue_yoy = _safe_float(latest_finance.get("revenue_yoy"))
        net_profit_yoy = _safe_float(latest_finance.get("net_profit_yoy"))
        roe = _safe_float(latest_finance.get("roe"))
        gross_margin = _safe_float(latest_finance.get("gross_margin"))
        percentile_50 = _safe_float(valuation.get("percentile_50"))

        positive_score = 0
        negative_score = 0
        reasons: list[str] = []
        risks: list[RiskFinding] = []
        agent_views: list[AgentView] = []

        event_signal = _summarize_event_signal(events)
        if event_signal["positive"] > event_signal["negative"] and event_signal["positive"] > 0:
            positive_score += 2
            reasons.append(f"结构化正向事件占优：{event_signal['positive']} 条")
        elif event_signal["negative"] > event_signal["positive"] and event_signal["negative"] > 0:
            negative_score += 2
            risks.append(RiskFinding(level="medium", message=f"结构化风险事件占优：{event_signal['negative']} 条"))

        if price is not None:
            reasons.append(f"最新价格 {price:.2f}")
        if change_pct is not None:
            if change_pct > 0:
                positive_score += 1
            elif change_pct < -3:
                negative_score += 1
                risks.append(RiskFinding(level="medium", message=f"近期涨跌幅偏弱：{change_pct:.2f}%"))
            reasons.append(f"日内涨跌幅 {change_pct:.2f}%")

        if ma5 is not None and ma20 is not None and latest_close is not None:
            if latest_close >= ma5 >= ma20:
                positive_score += 2
                reasons.append("价格站上短中期均线")
            elif latest_close < ma20:
                negative_score += 2
                risks.append(RiskFinding(level="medium", message="价格跌破中期均线"))

        if revenue_yoy is not None and net_profit_yoy is not None:
            if revenue_yoy > 0 and net_profit_yoy > 0:
                positive_score += 2
                reasons.append("营收和净利润同比为正")
            elif revenue_yoy < 0 or net_profit_yoy < 0:
                negative_score += 2
                risks.append(RiskFinding(level="high", message="最新财务同比指标存在负增长"))

        if roe is not None and roe >= 10:
            positive_score += 1
            reasons.append(f"ROE {roe:.2f}%")
        if gross_margin is not None and gross_margin >= 20:
            positive_score += 1
            reasons.append(f"毛利率 {gross_margin:.2f}%")
        if percentile_50 is not None and percentile_50 <= 30:
            positive_score += 1
            reasons.append(f"估值分位 {percentile_50:.2f}")

        if pe_ttm is not None and pe_ttm > 80:
            negative_score += 1
            risks.append(RiskFinding(level="medium", message=f"市盈率偏高：{pe_ttm:.2f}"))
        if pb is not None and pb > 10:
            negative_score += 1
            risks.append(RiskFinding(level="medium", message=f"市净率偏高：{pb:.2f}"))

        if predict_summary:
            first_predict = predict_summary[0] if isinstance(predict_summary, list) and predict_summary else {}
            eps = _safe_float(first_predict.get("eps"))
            if eps is not None and eps > 0:
                positive_score += 1
                reasons.append(f"机构一致预期 EPS {eps:.2f}")

        if iwencai_rows:
            positive_score += 1
            reasons.append(f"同花顺问财返回 {len(iwencai_rows)} 条匹配")

        if not reasons:
            reasons.append("已完成在线工具数据采集，但可解释信号仍然有限")
        if not risks:
            risks.append(RiskFinding(level="low", message="当前结论仍需盘后复核"))

        if positive_score >= 4 and positive_score > negative_score:
            action = DecisionAction.BUY
            summary = "在线工具数据整体偏正面，允许小仓位试错。"
        elif negative_score >= 4 and negative_score > positive_score:
            action = DecisionAction.WAIT
            summary = "在线工具数据偏弱，建议先观察或减仓。"
        elif positive_score > negative_score:
            action = DecisionAction.WATCH
            summary = "在线工具给出温和偏多信号，仍需等待更强确认。"
        elif negative_score > positive_score:
            action = DecisionAction.WAIT
            summary = "在线工具信号偏弱，暂不建议追涨。"
        else:
            action = DecisionAction.WATCH
            summary = "在线工具数据中性，保持观察。"

        if price is not None or change_pct is not None:
            agent_views.append(
                AgentView(
                    agent="Market Tool Lens",
                    conclusion=f"价格 {price if price is not None else 'n/a'}，涨跌幅 {change_pct if change_pct is not None else 'n/a'}，均线 {ma5 if ma5 is not None else 'n/a'}/{ma20 if ma20 is not None else 'n/a'}",
                )
            )
        if latest_finance:
            agent_views.append(
                AgentView(
                    agent="Fundamentals Tool Lens",
                    conclusion=f"营收同比 {revenue_yoy if revenue_yoy is not None else 'n/a'}，净利同比 {net_profit_yoy if net_profit_yoy is not None else 'n/a'}，ROE {roe if roe is not None else 'n/a'}",
                )
            )
        if events:
            agent_views.append(
                AgentView(
                    agent="News/Event Tool Lens",
                    conclusion=f"结构化事件：正向 {event_signal['positive']} 条，风险 {event_signal['negative']} 条，资讯 {len(news_items)} 条",
                )
            )

        _maybe_append(reasons, f"数据来源：{', '.join(data_sources) if data_sources else 'unknown'}")
        if quarterly:
            _maybe_append(reasons, f"季度财务样本 {len(quarterly)} 条")

        return AnalysisReport(
            task_id=task_id,
            stock=context.stock,
            status=AnalysisStatus.REPORT_READY,
            action=action,
            confidence=ConfidenceLevel.HIGH if not context.gaps else ConfidenceLevel.MEDIUM,
            summary=summary,
            reasons=reasons,
            risks=risks,
            agent_views=agent_views or [AgentView(agent="Tool Driven Engine", conclusion="已完成在线工具驱动分析")],
            data_context=context,
            engine_source="tool-driven",
            engine_mode="tool-driven",
        )

