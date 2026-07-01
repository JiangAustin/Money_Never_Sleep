import os

import pytest

from money_api.domains.analysis.contracts import BacktestPricePoint, StockIdentity
from money_api.domains.market_data.sina_kline import SinaKLineProvider


pytestmark = pytest.mark.network


@pytest.mark.skipif(os.getenv("MNS_RUN_NETWORK_SMOKE") != "1", reason="set MNS_RUN_NETWORK_SMOKE=1 to run network smoke")
def test_sina_kline_network_smoke() -> None:
    result = SinaKLineProvider(timeout_s=15.0).get_price_series(StockIdentity(code="600519", name="贵州茅台"), limit=5)

    assert result.ok is True, result.error_message
    assert len(result.data) >= 2
    assert all(isinstance(point, BacktestPricePoint) for point in result.data)
    assert all(point.date for point in result.data)
    assert all(point.close > 0 for point in result.data)
