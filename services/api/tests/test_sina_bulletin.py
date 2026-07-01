from money_api.domains.analysis.contracts import StockIdentity
from money_api.domains.market_data.sina_bulletin import SinaBulletinProvider, parse_sina_bulletin_html


def test_parse_sina_bulletin_html_returns_normalized_articles() -> None:
    html = """
    <html><body>
      <div class='datelist'>
        <ul>
          <li>2026-05-09 <a href='https://vip.stock.finance.sina.com.cn/bulletin/1'>协鑫能科：关于对控股子公司提供担保的进展公告</a></li>
          <li>2026-05-08 <a href='https://vip.stock.finance.sina.com.cn/bulletin/2'>协鑫能科：2026年5月8日投资者关系活动记录表</a></li>
        </ul>
      </div>
    </body></html>
    """

    articles = parse_sina_bulletin_html(html)

    assert articles == [
        {
            "title": "协鑫能科：关于对控股子公司提供担保的进展公告",
            "content": "",
            "time": "2026-05-09",
            "source": "新浪公告",
            "url": "https://vip.stock.finance.sina.com.cn/bulletin/1",
        },
        {
            "title": "协鑫能科：2026年5月8日投资者关系活动记录表",
            "content": "",
            "time": "2026-05-08",
            "source": "新浪公告",
            "url": "https://vip.stock.finance.sina.com.cn/bulletin/2",
        },
    ]


def test_sina_bulletin_provider_returns_provider_result() -> None:
    html = """
    <html><body><div class='datelist'><ul>
      <li>2026-05-09 <a href='https://vip.stock.finance.sina.com.cn/bulletin/1'>协鑫能科：关于对控股子公司提供担保的进展公告</a></li>
    </ul></div></body></html>
    """
    provider = SinaBulletinProvider(transport=lambda url: html)

    result = provider.get_news(StockIdentity(code="002015", name="协鑫能科"))

    assert result.ok is True
    assert result.source == "sina-bulletin"
    assert result.data[0]["source"] == "新浪公告"


def test_sina_bulletin_provider_handles_transport_failure() -> None:
    provider = SinaBulletinProvider(transport=lambda url: (_ for _ in ()).throw(RuntimeError("boom")))

    result = provider.get_news(StockIdentity(code="002015", name="协鑫能科"))

    assert result.ok is False
    assert result.data == []
    assert result.error_type == "RuntimeError"