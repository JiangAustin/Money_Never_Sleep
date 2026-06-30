# 阶段 2 真实 A 股数据层实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 建立真实 A 股数据层的稳定契约、诊断和最小腾讯行情接入，让单股分析在默认离线测试稳定的前提下具备一个可手动验证的真实 quote smoke 路径。

**架构：** 先扩展数据契约和 `DataContextBuilder`，让 provider 调用产生结构化 `ProviderResult` 和 diagnostics；再实现纯函数腾讯 quote parser；最后用可注入 transport 的 `TencentQuoteProvider` 和可选 smoke 验证真实网络链路。默认 API 仍使用离线 fixture，避免测试依赖网络。

**技术栈：** Python 3.10+、dataclasses、Protocol、pytest、urllib/request 注入式 transport、当前 `services/api/money_api` 包结构。

---

## 范围切分

本计划只覆盖阶段 2 的最小真实数据层：

- ProviderResult 和 diagnostics 契约。
- `DataContext` diagnostics 字段。
- `DataContextBuilder` 从 provider result 构建 context。
- 腾讯 quote raw response parser。
- 可注入 transport 的腾讯 quote provider。
- provider 失败时进入 gaps 和 diagnostics。
- 默认离线测试和可选网络 smoke。

不实现：完整 TradingAgents 数据层、DSA 完整 DataFetcherManager、真实 K 线 provider、新闻聚合、数据库缓存、Web/桌面 UI。

## 文件结构

- 创建：`services/api/money_api/domains/market_data/provider_results.py`
  定义 `ProviderResult`、`ProviderDiagnostic` 和标准 diagnostics 序列化。
- 修改：`services/api/money_api/domains/analysis/contracts.py`
  为 `DataContext` 增加 `diagnostics`，为 `AnalysisReport.to_dict()` 暴露 `data_diagnostics`。
- 修改：`services/api/money_api/domains/analysis/context_builder.py`
  让 provider getter 返回 `ProviderResult`，并从 result 中提取 data/gaps/diagnostics。
- 创建：`services/api/money_api/domains/market_data/tencent_quote.py`
  实现腾讯行情前缀、raw line parser、网络 provider。
- 创建：`services/api/tests/test_provider_results.py`
- 修改：`services/api/tests/test_analysis_contracts.py`
- 修改：`services/api/tests/test_context_builder.py`
- 创建：`services/api/tests/test_tencent_quote.py`
- 修改：`services/api/tests/test_analysis_api.py`
- 创建：`services/api/tests/test_tencent_quote_smoke.py`
- 修改：`README.md`
- 修改：`docs/stages.md`

---

### 任务 1：ProviderResult 与 diagnostics 契约

**文件：**
- 创建：`services/api/money_api/domains/market_data/provider_results.py`
- 修改：`services/api/money_api/domains/analysis/contracts.py`
- 测试：`services/api/tests/test_provider_results.py`
- 测试：`services/api/tests/test_analysis_contracts.py`

- [ ] **步骤 1：编写失败的测试**

```python
from money_api.domains.analysis.contracts import AnalysisReport, AnalysisStatus, ConfidenceLevel, DataContext, DecisionAction, StockIdentity
from money_api.domains.market_data.provider_results import ProviderDiagnostic, ProviderResult


def test_provider_result_success_to_diagnostic() -> None:
    result = ProviderResult(kind="quote", source="static", ok=True, data={"price": 1688.0})

    assert result.to_diagnostic() == {
        "kind": "quote",
        "source": "static",
        "ok": True,
        "error_type": None,
        "error_message": None,
        "fetched_at": None,
        "is_stale": False,
    }


def test_provider_result_failure_to_gap_reason() -> None:
    result = ProviderResult(kind="quote", source="tencent", ok=False, data={}, error_type="TimeoutError", error_message="timeout")

    assert result.gap_name == "quote"
    assert result.to_diagnostic()["error_message"] == "timeout"


def test_analysis_report_exposes_data_diagnostics() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    diagnostic = ProviderDiagnostic(kind="quote", source="tencent", ok=False, error_type="TimeoutError", error_message="timeout")
    context = DataContext(stock=stock, gaps=["quote"], diagnostics=[diagnostic.to_dict()])
    report = AnalysisReport(
        task_id="task-1",
        stock=stock,
        status=AnalysisStatus.REPORT_READY,
        action=DecisionAction.WATCH,
        confidence=ConfidenceLevel.LOW,
        summary="partial",
        reasons=[],
        risks=[],
        agent_views=[],
        data_context=context,
    )

    assert report.to_dict()["data_diagnostics"] == [diagnostic.to_dict()]
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_provider_results.py services/api/tests/test_analysis_contracts.py -v`
预期：FAIL，报错包含 `ModuleNotFoundError: No module named 'money_api.domains.market_data.provider_results'` 或 `DataContext.__init__()` 不接受 `diagnostics`。

- [ ] **步骤 3：实现 ProviderResult 和 diagnostics 字段**

创建 `provider_results.py`：

```python
"""Provider result contracts for market data collection."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProviderDiagnostic:
    kind: str
    source: str
    ok: bool
    error_type: str | None = None
    error_message: str | None = None
    fetched_at: str | None = None
    is_stale: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "source": self.source,
            "ok": self.ok,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "fetched_at": self.fetched_at,
            "is_stale": self.is_stale,
        }


@dataclass(frozen=True)
class ProviderResult:
    kind: str
    source: str
    ok: bool
    data: dict[str, Any] | list[dict[str, Any]] = field(default_factory=dict)
    error_type: str | None = None
    error_message: str | None = None
    fetched_at: str | None = None
    is_stale: bool = False

    @property
    def gap_name(self) -> str:
        return self.kind

    def to_diagnostic(self) -> dict[str, Any]:
        return ProviderDiagnostic(
            kind=self.kind,
            source=self.source,
            ok=self.ok,
            error_type=self.error_type,
            error_message=self.error_message,
            fetched_at=self.fetched_at,
            is_stale=self.is_stale,
        ).to_dict()
```

修改 `DataContext` 增加：

```python
diagnostics: list[dict[str, Any]] = field(default_factory=list)
```

修改 `AnalysisReport.to_dict()` 增加：

```python
"data_diagnostics": list(self.data_context.diagnostics),
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_provider_results.py services/api/tests/test_analysis_contracts.py -v`
预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/domains/market_data/provider_results.py services/api/money_api/domains/analysis/contracts.py services/api/tests/test_provider_results.py services/api/tests/test_analysis_contracts.py
git commit -m "feat: add provider diagnostics contracts" -m "Outline:
- Define ProviderResult and ProviderDiagnostic for market data collection.
- Add diagnostics to DataContext and report serialization.
- Cover success and failure provider diagnostic payloads."
```

---

### 任务 2：DataContextBuilder 使用 ProviderResult

**文件：**
- 修改：`services/api/money_api/domains/analysis/context_builder.py`
- 测试：`services/api/tests/test_context_builder.py`

- [ ] **步骤 1：编写失败的测试**

```python
from money_api.domains.analysis.context_builder import DataContextBuilder, StaticMarketDataProvider
from money_api.domains.analysis.contracts import StockIdentity
from money_api.domains.market_data.provider_results import ProviderResult


class FailingProvider(StaticMarketDataProvider):
    def get_quote(self, stock: StockIdentity) -> ProviderResult:
        return ProviderResult(kind="quote", source="failing", ok=False, data={}, error_type="RuntimeError", error_message="boom")


def test_context_builder_records_provider_diagnostics() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    context = DataContextBuilder(FailingProvider()).build(stock)

    assert "quote" in context.gaps
    assert context.diagnostics[0]["source"] == "failing"
    assert context.diagnostics[0]["error_message"] == "boom"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_context_builder.py -v`
预期：FAIL，当前 builder 仍按 raw dict/list 处理 provider 返回值。

- [ ] **步骤 3：更新 provider 协议和静态 provider**

将 `MarketDataProvider` 四个 getter 改为返回 `ProviderResult`。`StaticMarketDataProvider` getter 返回：

```python
ProviderResult(kind="quote", source="static", ok=bool(self.quote), data=dict(self.quote))
```

`get_news()` 返回：

```python
ProviderResult(kind="news", source="static", ok=bool(self.news), data=list(self.news))
```

`DataContextBuilder.build()` 先收集四个 result，再取 `result.data`，`not result.ok or not result.data` 时记录 gap，并将每个 result 的 diagnostic 放入 `DataContext.diagnostics`。

- [ ] **步骤 4：更新原有测试预期**

保留现有 context builder 测试语义：全数据时 gaps 为空；只有 quote 时 gaps 为 `technicals/fundamentals/news`；全空时四类 gaps；静态 provider 仍保护 fixture 状态。

- [ ] **步骤 5：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_context_builder.py services/api/tests/test_analysis_api.py -v`
预期：PASS。

- [ ] **步骤 6：Commit**

```bash
git add services/api/money_api/domains/analysis/context_builder.py services/api/tests/test_context_builder.py
git commit -m "feat: build data context from provider results" -m "Outline:
- Update market data providers to return ProviderResult objects.
- Populate DataContext data, gaps, and diagnostics from provider results.
- Preserve deterministic static provider behavior and existing context tests."
```

---

### 任务 3：腾讯行情 parser

**文件：**
- 创建：`services/api/money_api/domains/market_data/tencent_quote.py`
- 测试：`services/api/tests/test_tencent_quote.py`

- [ ] **步骤 1：编写失败的测试**

```python
from money_api.domains.market_data.tencent_quote import get_tencent_market_prefix, parse_tencent_quote_line


def test_get_tencent_market_prefix() -> None:
    assert get_tencent_market_prefix("600519") == "sh"
    assert get_tencent_market_prefix("000001") == "sz"
    assert get_tencent_market_prefix("920001") == "sh"
    assert get_tencent_market_prefix("830000") == "bj"


def test_parse_tencent_quote_line() -> None:
    values = [""] * 53
    values[1] = "贵州茅台"
    values[3] = "1688.00"
    values[4] = "1680.00"
    values[5] = "1681.00"
    values[32] = "1.23"
    values[33] = "1700.00"
    values[34] = "1670.00"
    values[38] = "0.56"
    values[39] = "28.50"
    values[44] = "21000.00"
    values[46] = "9.10"
    values[47] = "1848.00"
    values[48] = "1512.00"
    raw = 'v_sh600519="' + "~".join(values) + '";'

    quote = parse_tencent_quote_line("600519", raw)

    assert quote["code"] == "600519"
    assert quote["name"] == "贵州茅台"
    assert quote["price"] == 1688.0
    assert quote["change_pct"] == 1.23
    assert quote["source"] == "tencent"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tencent_quote.py -v`
预期：FAIL，模块不存在。

- [ ] **步骤 3：实现纯 parser**

实现 `get_tencent_market_prefix(code: str) -> str` 和 `parse_tencent_quote_line(code: str, raw_line: str) -> dict[str, object]`。

解析字段：`name`、`price`、`last_close`、`open`、`change_pct`、`high`、`low`、`turnover_pct`、`pe_ttm`、`market_cap`、`pb`、`limit_up`、`limit_down`、`source`。

无效 raw line 抛出 `ValueError("无法解析腾讯行情: <code>")`。

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tencent_quote.py -v`
预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/domains/market_data/tencent_quote.py services/api/tests/test_tencent_quote.py
git commit -m "feat: parse Tencent quote payloads" -m "Outline:
- Add Tencent market prefix detection for A-share symbols.
- Parse Tencent quote raw payloads into the standard quote shape.
- Cover parser behavior with deterministic fixture tests."
```

---

### 任务 4：TencentQuoteProvider

**文件：**
- 修改：`services/api/money_api/domains/market_data/tencent_quote.py`
- 测试：`services/api/tests/test_tencent_quote.py`

- [ ] **步骤 1：编写失败的测试**

```python
from money_api.domains.analysis.contracts import StockIdentity
from money_api.domains.market_data.tencent_quote import TencentQuoteProvider


def test_tencent_quote_provider_uses_injected_transport() -> None:
    def transport(url: str) -> str:
        assert "sh600519" in url
        values = [""] * 53
        values[1] = "贵州茅台"
        values[3] = "1688.00"
        return 'v_sh600519="' + "~".join(values) + '";'

    result = TencentQuoteProvider(transport=transport).get_quote(StockIdentity(code="600519", name="贵州茅台"))

    assert result.ok is True
    assert result.source == "tencent"
    assert result.data["price"] == 1688.0


def test_tencent_quote_provider_returns_failure_result() -> None:
    def transport(url: str) -> str:
        raise TimeoutError("timeout")

    result = TencentQuoteProvider(transport=transport).get_quote(StockIdentity(code="600519", name="贵州茅台"))

    assert result.ok is False
    assert result.error_type == "TimeoutError"
    assert result.error_message == "timeout"
```

- [ ] **步骤 2：实现 provider**

`TencentQuoteProvider` 构造参数：

```python
def __init__(self, transport: Callable[[str], str] | None = None, timeout_s: float = 10.0): ...
```

默认 transport 使用 `urllib.request`，读取 GBK 并返回字符串。`get_quote(stock)` 返回 `ProviderResult(kind="quote", source="tencent", ok=True/False, data=...)`。

- [ ] **步骤 3：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tencent_quote.py -v`
预期：PASS。

- [ ] **步骤 4：Commit**

```bash
git add services/api/money_api/domains/market_data/tencent_quote.py services/api/tests/test_tencent_quote.py
git commit -m "feat: add Tencent quote provider" -m "Outline:
- Add an injectable Tencent quote provider around the parser.
- Return ProviderResult diagnostics for success and failure paths.
- Keep unit tests deterministic through fake transports."
```

---

### 任务 5：默认 API 服务保持离线，支持腾讯 provider 工厂

**文件：**
- 修改：`services/api/money_api/api/v1/router.py`
- 测试：`services/api/tests/test_analysis_api.py`

- [ ] **步骤 1：编写失败的测试**

```python
from money_api.api.v1.router import build_default_analysis_service, build_tencent_quote_analysis_service


def test_default_analysis_service_stays_offline() -> None:
    payload = build_default_analysis_service().create_single_stock_analysis("贵州茅台", "请全面分析").to_dict()

    assert payload["stock"]["code"] == "600519"
    assert payload["data_diagnostics"][0]["source"] == "static"


def test_tencent_quote_service_factory_accepts_transport() -> None:
    def transport(url: str) -> str:
        values = [""] * 53
        values[1] = "贵州茅台"
        values[3] = "1688.00"
        return 'v_sh600519="' + "~".join(values) + '";'

    service = build_tencent_quote_analysis_service(transport=transport)
    payload = service.create_single_stock_analysis("贵州茅台", "请全面分析").to_dict()

    assert payload["data_diagnostics"][0]["source"] == "tencent"
```

- [ ] **步骤 2：实现工厂**

保留 `_analysis_service = build_default_analysis_service()` 使用 static provider。新增 `build_tencent_quote_analysis_service(transport=None)`，只替换 quote provider，technicals/fundamentals/news 仍用 static fixture 或空 fixture。

- [ ] **步骤 3：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_analysis_api.py services/api/tests/test_tencent_quote.py -v`
预期：PASS。

- [ ] **步骤 4：Commit**

```bash
git add services/api/money_api/api/v1/router.py services/api/tests/test_analysis_api.py
git commit -m "feat: add Tencent quote service factory" -m "Outline:
- Keep the default API analysis service offline and deterministic.
- Add an optional Tencent quote analysis service factory.
- Verify static and Tencent-backed diagnostics through API-level tests."
```

---

### 任务 6：可选腾讯网络 smoke

**文件：**
- 创建：`services/api/tests/test_tencent_quote_smoke.py`
- 修改：`pyproject.toml`
- 修改：`docs/stages.md`

- [ ] **步骤 1：编写 smoke 测试**

```python
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
```

- [ ] **步骤 2：注册 pytest marker**

在 `pyproject.toml` 增加：

```toml
markers = [
  "network: tests requiring external network access",
]
```

如果已有 marker 配置，追加 `network`，不要破坏现有配置。

- [ ] **步骤 3：更新阶段文档 smoke 命令**

在 `docs/stages.md` 阶段 2 验收说明附近增加：

```bash
MNS_RUN_NETWORK_SMOKE=1 PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tencent_quote_smoke.py -v
```

- [ ] **步骤 4：运行默认测试**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -v`
预期：PASS，network smoke 默认 skip。

- [ ] **步骤 5：Commit**

```bash
git add services/api/tests/test_tencent_quote_smoke.py pyproject.toml docs/stages.md
git commit -m "test: add optional Tencent quote smoke" -m "Outline:
- Add an opt-in network smoke for Tencent quote retrieval.
- Register the network pytest marker.
- Document the manual smoke command without making it a default test dependency."
```

---

### 任务 7：文档、README 与最终验证

**文件：**
- 修改：`README.md`
- 修改：`docs/stages.md`

- [ ] **步骤 1：更新 README 当前实现切片**

在 `README.md` 当前实现切片后补充阶段 2 数据层说明：

```markdown

下一阶段正在建设真实 A 股数据层：默认测试保持离线，通过 ProviderResult 和 diagnostics 记录数据来源、失败原因和 data gaps；腾讯行情作为第一条可选真实 smoke 路径。
```

- [ ] **步骤 2：更新 stages 状态**

将阶段 2 状态从 `进行中` 更新为 `已完成`，并记录：

- 默认离线 API 测试结果。
- 腾讯 quote smoke 命令。
- 下一阶段建议：TradingAgents 深度引擎接入前，先审查数据上下文是否满足其工具输入。

- [ ] **步骤 3：运行最终验证**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -v`
预期：PASS。

运行：`git diff --check README.md docs/stages.md docs/superpowers/plans/2026-07-01-stage-2-a-share-data-layer.md`
预期：退出码 0，无输出。

- [ ] **步骤 4：Commit**

```bash
git add README.md docs/stages.md
git commit -m "docs: document stage 2 data layer completion" -m "Outline:
- Update README with the real A-share data layer direction.
- Mark stage 2 complete in the living stage roadmap.
- Record validation and the optional Tencent quote smoke command."
```

---

## 计划自检结果

### 规格覆盖度

- ProviderResult 和 diagnostics：任务 1 覆盖。
- DataContextBuilder fallback/gaps/diagnostics：任务 2 覆盖。
- 腾讯 quote parser：任务 3 覆盖。
- 腾讯 quote provider：任务 4 覆盖。
- 默认离线 API 与可选腾讯工厂：任务 5 覆盖。
- 可选真实网络 smoke：任务 6 覆盖。
- README 和阶段文档更新：任务 7 覆盖。
- TradingAgents 完整数据层、真实 K 线、新闻聚合、数据库缓存：明确不属于本计划。

### 占位符扫描

计划正文不使用占位符红旗表达；每个实现步骤都包含目标文件、示例测试、实现方向、命令和提交大纲。

### 类型一致性

- `ProviderResult` 在任务 1 定义，任务 2-5 均使用同一路径 `money_api.domains.market_data.provider_results`。
- `DataContext.diagnostics` 在任务 1 定义，任务 2 和任务 5 通过 `AnalysisReport.to_dict()["data_diagnostics"]` 验证。
- `TencentQuoteProvider.get_quote(stock)` 在任务 4 定义，任务 5 和任务 6 复用相同签名。