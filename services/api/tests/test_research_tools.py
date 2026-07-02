import json

from money_api.api.v1.router import build_runtime_research_tool_service


def _fake_tencent_transport(url: str) -> str:
    values = [""] * 53
    values[1] = "贵州茅台"
    values[3] = "1688.00"
    values[32] = "2.50"
    values[39] = "28.50"
    values[46] = "9.10"
    return 'v_sh600519="' + "~".join(values) + '";'


def _fake_kline_transport(url: str) -> str:
    return json.dumps(
        [
            {"day": "2026-06-01", "close": 1600.0},
            {"day": "2026-06-02", "close": 1610.0},
            {"day": "2026-06-03", "close": 1620.0},
            {"day": "2026-06-04", "close": 1630.0},
            {"day": "2026-06-05", "close": 1640.0},
            {"day": "2026-06-06", "close": 1650.0},
        ],
        ensure_ascii=False,
    )


def _fake_eastmoney_transport(url: str) -> str:
    if "RPT_PCF10_FINANCEMAINFINADATA" in url:
        payload = {
            "result": {
                "data": [
                    {
                        "REPORT_DATE": "2026-03-31",
                        "REPORT_TYPE": "Q1",
                        "EPSJB": 8.88,
                        "BPS": 42.0,
                        "TOTAL_OPERATEINCOME": 1000.0,
                        "TOTAL_OPERATEINCOME_LAST": 880.0,
                        "PARENT_NETPROFIT": 380.0,
                        "PARENT_NETPROFIT_LAST": 320.0,
                        "TOTALOPERATEREVETZ": 13.64,
                        "PARENTNETPROFITTZ": 18.75,
                        "ROEJQ": 18.0,
                        "XSMLL": 35.0,
                        "ZCFZL": 28.0,
                        "TOTAL_SHARE": 1250.0,
                        "FREE_SHARE": 980.0,
                    }
                ]
            }
        }
    elif "RPT_F10_QTR_MAINFINADATA" in url:
        payload = {"result": {"data": [{"REPORT_DATE": "2026-03-31", "EPSJB": 2.1, "BPS": 41.0, "TOTALOPERATEREVE": 300.0, "PARENTNETPROFIT": 110.0, "TOTALOPERATEREVETZ": 11.0, "PARENTNETPROFITTZ": 12.0, "ROE_DILUTED": 4.5, "GROSS_PROFIT_RATIO": 33.0}]}}
    elif "RPT_HSF10_RESPREDICT_STATISTICS" in url:
        payload = {"result": {"data": [{"YEAR": "2026", "EPS": 8.8, "EPS_RATIO": 15.0, "PE": 27.5}]}}
    elif "RPT_STOCKVALUATIONTANTILE" in url:
        payload = {"result": {"data": [{"STATISTICS_CYCLE": 3, "INDEX_TYPE": 1, "PERCENTILE_THIRTY": 22.0, "PERCENTILE_FIFTY": 30.0, "PERCENTILE_SEVENTY": 45.0}]}}
    elif "RPT_MARGIN_STATISTICS_STOCKS" in url:
        payload = {"result": {"data": [{"TRADE_DATE": "2026-07-01", "FIN_BUY_AMT": 100.0, "FIN_REPAY_AMT": 60.0, "FIN_BALANCE": 480.0, "LOAN_SELL_VOL": 1.0, "LOAN_REPAY_VOL": 0.5, "LOAN_BALANCE": 20.0}]}}
    elif "RPT_STOCK_MAINFUND_FLOW" in url:
        payload = {"result": {"data": [{"TRADE_DATE": "2026-07-01", "MAIN_NET_INFLOW": 120.0, "MAIN_NET_INFLOW_RATE": 1.8, "MAIN_BUY": 240.0, "MAIN_SELL": 120.0}]}}
    elif "RPT_DAILYBILLBOARD_DETAILS" in url:
        payload = {"result": {"data": [{"TRADE_DATE": "2026-07-01", "BUY_AMT": 100.0, "SELL_AMT": 62.0, "NET_AMT": 38.0, "ORGAN_AMT": 15.0}]}}
    elif "RPT_STOCK_LIFTING_SCHEDULE" in url:
        payload = {"result": {"data": [{"UNLOCK_DATE": "2026-07-15", "UNLOCK_NUM": 1000.0, "UNLOCK_VALUE": 32000.0, "UNLOCK_RATIO": 3.2}]}}
    else:
        payload = {"result": {"data": []}}
    return json.dumps(payload, ensure_ascii=False)


def _fake_iwencai_transport(url: str) -> str:
    return json.dumps(
        {
            "status_code": 0,
            "status_msg": "ok",
            "code_count": 1,
            "datas": [{"股票代码": "600519", "机构评分": 88, "营业总收入": 1000.0}],
            "chunks_info": [],
        },
        ensure_ascii=False,
    )


def test_research_context_collects_sources_and_events() -> None:
    service = build_runtime_research_tool_service(
        quote_transport=_fake_tencent_transport,
        kline_transport=_fake_kline_transport,
        eastmoney_transport=_fake_eastmoney_transport,
        iwencai_api_key="test-key",
        iwencai_transport=_fake_iwencai_transport,
        news_transport=lambda url: (
            'callback({"result":{"cmsArticleWebOld":[{"title":"茅台业绩稳健","content":"季度表现稳定",'
            '"date":"2026-07-01 09:30:00","mediaName":"东方财富","url":"https://example.com/news/1"}]}})'
        ),
        flash_transport=lambda url: {"data": {"roll_data": [{"title": "央行公开市场操作", "brief": "今日开展逆回购操作", "ctime": "1782879000"}]}},
        bulletin_transport=lambda url: """
        <html><body><div class='datelist'><ul>
          <li>2026-05-09 <a href='https://vip.stock.finance.sina.com.cn/bulletin/1'>协鑫能科：关于对控股子公司提供担保的进展公告</a></li>
        </ul></div></body></html>
        """,
    )

    snapshot = service.build_context("贵州茅台").to_dict()

    assert snapshot["stock"]["code"] == "600519"
    assert snapshot["data_sources"] == ["tencent", "sina", "eastmoney+iwencai", "eastmoney+cls+sina-bulletin"]
    assert snapshot["data_context"]["events"][0]["event_type"] == "guarantee"
    assert snapshot["source_summary"][2]["source"].startswith("eastmoney+iwencai")


def test_research_fundamentals_exposes_provider_chain() -> None:
    service = build_runtime_research_tool_service(
        quote_transport=_fake_tencent_transport,
        kline_transport=_fake_kline_transport,
        eastmoney_transport=_fake_eastmoney_transport,
        iwencai_api_key="test-key",
        iwencai_transport=_fake_iwencai_transport,
    )

    payload = service.get_fundamentals("贵州茅台")

    assert payload["stock"]["code"] == "600519"
    assert payload["result"]["source"] == "eastmoney+iwencai"
    assert payload["result"]["ok"] is True
    assert payload["result"]["data"]["latest_finance"]["report_date"] == "2026-03-31"
    assert payload["result"]["data"]["rows"][0]["股票代码"] == "600519"


def test_research_quote_returns_diagnostic_payload() -> None:
    service = build_runtime_research_tool_service(
        quote_transport=_fake_tencent_transport,
        kline_transport=_fake_kline_transport,
        eastmoney_transport=_fake_eastmoney_transport,
    )

    payload = service.get_quote("贵州茅台")

    assert payload["stock"]["code"] == "600519"
    assert payload["result"]["source"] == "tencent"
    assert payload["result"]["ok"] is True


def test_research_extras_exposes_capital_flow_longhubang_and_unlocks() -> None:
    service = build_runtime_research_tool_service(
        quote_transport=_fake_tencent_transport,
        kline_transport=_fake_kline_transport,
        eastmoney_transport=_fake_eastmoney_transport,
    )

    capital_flow = service.get_capital_flow("贵州茅台")
    longhubang = service.get_longhubang("贵州茅台")
    unlocks = service.get_unlocks("贵州茅台")

    assert capital_flow["result"]["ok"] is True
    assert capital_flow["result"]["data"]["rows"][0]["MAIN_NET_INFLOW"] == 120.0
    assert longhubang["result"]["ok"] is True
    assert longhubang["result"]["data"]["rows"][0]["NET_AMT"] == 38.0
    assert unlocks["result"]["ok"] is True
    assert unlocks["result"]["data"]["rows"][0]["UNLOCK_DATE"] == "2026-07-15"
