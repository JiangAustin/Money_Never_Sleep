import os

import pytest

from money_api.api.v1.router import build_tradingagents_analysis_service
from money_api.integrations.tradingagents_runner import TradingAgentsGraphRunner


pytestmark = pytest.mark.external_engine


@pytest.mark.skipif(os.getenv("MNS_RUN_TRADINGAGENTS_SMOKE") != "1", reason="set MNS_RUN_TRADINGAGENTS_SMOKE=1 to run TradingAgents smoke")
def test_tradingagents_engine_smoke() -> None:
    service = build_tradingagents_analysis_service(runner=TradingAgentsGraphRunner())
    payload = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议").to_dict()

    assert payload["stock"]["code"] == "600519"
    assert payload["status"] in {"report_ready", "failed"}
    assert payload["data_diagnostics"][-1]["source"] == "tradingagents"
