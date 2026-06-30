import os

import pytest

from money_api.domains.analysis.contracts import StockIdentity
from money_api.domains.market_data.tencent_quote import TencentQuoteProvider


pytestmark = pytest.mark.network


@pytest.mark.skipif(os.getenv("MNS_RUN_NETWORK_SMOKE") != "1", reason="set MNS_RUN_NETWORK_SMOKE=1 to run network smoke")
def test_tencent_quote_network_smoke() -> None:
    result = TencentQuoteProvider().get_quote(StockIdentity(code="600519", name="贵州茅台"))

    assert result.ok is True
    assert result.data["code"] == "600519"
    assert result.data["price"] is not None
