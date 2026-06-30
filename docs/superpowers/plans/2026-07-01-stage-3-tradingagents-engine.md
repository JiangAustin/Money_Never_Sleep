# 阶段 3 TradingAgents 深度引擎接入实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将 TradingAgents-astock 封装为 Money_Never_sleep 的可选 `DeepResearchEngine` 实现，同时保持默认 API 和默认测试离线稳定。

**架构：** 新增 TradingAgents adapter 层：`TradingAgentsDeepResearchEngine` 只依赖小型 runner 协议，fake runner 用于离线测试，真实 runner 懒加载 `TradingAgentsGraph`。API 层新增 opt-in 服务工厂，默认服务继续使用 `MockDeepResearchEngine`。

**技术栈：** Python 3.10+、dataclasses、Protocol、pytest、importlib、当前 `services/api/money_api` 包结构。

---

## 范围切分

本计划只覆盖阶段 3 的最小真实引擎接入边界：

- TradingAgents request/result 契约。
- Fake runner 与 `TradingAgentsDeepResearchEngine`。
- runner 失败到 `AnalysisReport` 的结构化映射。
- 真实 `TradingAgentsGraphRunner` 壳，默认不导入、不调用。
- API 可选工厂。
- opt-in smoke 与文档更新。

不实现：Web/桌面切换、异步任务队列、报告持久化、成本看板、真实 prompt 调优、TradingAgents 源码迁移。

## 文件结构

- 创建：`services/api/money_api/domains/analysis/tradingagents_engine.py`
  定义 `TradingAgentsRunRequest`、`TradingAgentsRunResult`、`TradingAgentsRunner`、`FakeTradingAgentsRunner`、`TradingAgentsDeepResearchEngine`。
- 创建：`services/api/money_api/integrations/tradingagents_runner.py`
  定义真实 `TradingAgentsGraphRunner` 壳，懒加载 TradingAgents-astock。
- 创建：`services/api/money_api/integrations/__init__.py`
  标记 integrations 包。
- 修改：`services/api/money_api/api/v1/router.py`
  新增 `build_tradingagents_analysis_service(...)`，默认服务不变。
- 修改：`services/api/money_api/core/config.py`
  增加非 secret 的 TradingAgents 配置读取。
- 修改：`.env.example`
  增加 opt-in 开关、路径和缓存/结果目录示例，不写 API key。
- 创建：`services/api/tests/test_tradingagents_engine.py`
- 创建：`services/api/tests/test_tradingagents_runner.py`
- 修改：`services/api/tests/test_analysis_api.py`
- 创建：`services/api/tests/test_tradingagents_smoke.py`
- 修改：`pyproject.toml`
  如已有 `network` marker，则追加 `external_engine` marker。
- 修改：`README.md`
- 修改：`docs/stages.md`

---

### 任务 1：TradingAgents run 契约与 fake runner

**文件：**

- 创建：`services/api/money_api/domains/analysis/tradingagents_engine.py`
- 测试：`services/api/tests/test_tradingagents_engine.py`

- [ ] **步骤 1：编写失败的测试**

```python
from money_api.domains.analysis.contracts import DataContext, StockIdentity
from money_api.domains.analysis.tradingagents_engine import (
    FakeTradingAgentsRunner,
    TradingAgentsRunRequest,
    TradingAgentsRunResult,
)


def test_run_request_from_context_captures_snapshot() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    context = DataContext(
        stock=stock,
        quote={"price": 1688.0},
        technicals={"ma5": 1660.0},
        fundamentals={"pe_ttm": 28.5},
        news=[{"title": "业绩稳定"}],
        gaps=["news"],
        diagnostics=[{"kind": "quote", "source": "tencent", "ok": True}],
    )

    request = TradingAgentsRunRequest.from_context("task-1", context, trade_date="2026-07-01")

    assert request.task_id == "task-1"
    assert request.code == "600519"
    assert request.context_snapshot["quote"]["price"] == 1688.0
    assert request.context_snapshot["gaps"] == ["news"]
    assert request.diagnostics == [{"kind": "quote", "source": "tencent", "ok": True}]


def test_fake_runner_returns_success_result() -> None:
    request = TradingAgentsRunRequest(
        task_id="task-1",
        code="600519",
        name="贵州茅台",
        market="cn",
        trade_date="2026-07-01",
        context_snapshot={},
        diagnostics=[],
    )

    result = FakeTradingAgentsRunner().run(request)

    assert isinstance(result, TradingAgentsRunResult)
    assert result.ok is True
    assert result.source == "fake-tradingagents"
    assert result.final_decision == "WATCH"
    assert result.agent_reports["market"]
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tradingagents_engine.py -v`

预期：FAIL，报错包含 `ModuleNotFoundError: No module named 'money_api.domains.analysis.tradingagents_engine'`。

- [ ] **步骤 3：实现契约与 fake runner**

在 `services/api/money_api/domains/analysis/tradingagents_engine.py` 写入：

```python
"""TradingAgents engine adapter contracts."""

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Protocol

from money_api.domains.analysis.contracts import DataContext


@dataclass(frozen=True)
class TradingAgentsRunRequest:
    task_id: str
    code: str
    name: str
    market: str
    trade_date: str
    context_snapshot: dict[str, Any]
    diagnostics: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_context(cls, task_id: str, context: DataContext, trade_date: str | None = None) -> "TradingAgentsRunRequest":
        return cls(
            task_id=task_id,
            code=context.stock.code,
            name=context.stock.name,
            market=context.stock.market,
            trade_date=trade_date or date.today().isoformat(),
            context_snapshot={
                "quote": dict(context.quote),
                "technicals": dict(context.technicals),
                "fundamentals": dict(context.fundamentals),
                "news": list(context.news),
                "gaps": list(context.gaps),
            },
            diagnostics=list(context.diagnostics),
        )


@dataclass(frozen=True)
class TradingAgentsRunResult:
    ok: bool
    source: str
    final_decision: str = "WATCH"
    summary: str = ""
    agent_reports: dict[str, str] = field(default_factory=dict)
    raw_state: dict[str, Any] = field(default_factory=dict)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    error_type: str | None = None
    error_message: str | None = None


class TradingAgentsRunner(Protocol):
    def run(self, request: TradingAgentsRunRequest) -> TradingAgentsRunResult: ...


class FakeTradingAgentsRunner:
    def run(self, request: TradingAgentsRunRequest) -> TradingAgentsRunResult:
        return TradingAgentsRunResult(
            ok=True,
            source="fake-tradingagents",
            final_decision="WATCH",
            summary=f"{request.name} fake TradingAgents 分析完成。",
            agent_reports={
                "market": "离线市场分析结果",
                "fundamentals": "离线基本面分析结果",
                "risk": "离线风险辩论结果",
            },
            diagnostics=[{"kind": "deep_engine", "source": "fake-tradingagents", "ok": True}],
        )
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tradingagents_engine.py -v`

预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/domains/analysis/tradingagents_engine.py services/api/tests/test_tradingagents_engine.py
git commit -m "feat: add TradingAgents run contracts" -m "Outline:
- Define request/result contracts for TradingAgents engine execution.
- Add a runner protocol and deterministic fake runner.
- Capture DataContext snapshots and diagnostics for adapter inputs."
```

---

### 任务 2：TradingAgentsDeepResearchEngine 映射成功结果

**文件：**

- 修改：`services/api/money_api/domains/analysis/tradingagents_engine.py`
- 测试：`services/api/tests/test_tradingagents_engine.py`

- [ ] **步骤 1：编写失败的测试**

追加测试：

```python
from money_api.domains.analysis.tradingagents_engine import TradingAgentsDeepResearchEngine


def test_tradingagents_engine_maps_success_result_to_report() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    context = DataContext(stock=stock, quote={"price": 1688.0})

    report = TradingAgentsDeepResearchEngine(FakeTradingAgentsRunner()).analyze("task-1", context)

    assert report.task_id == "task-1"
    assert report.status.value == "report_ready"
    assert report.action.value == "watch"
    assert report.confidence.value == "medium"
    assert report.summary == "贵州茅台 fake TradingAgents 分析完成。"
    assert report.agent_views[0].agent == "TradingAgents market"
    assert report.data_context.diagnostics[-1]["source"] == "fake-tradingagents"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tradingagents_engine.py::test_tradingagents_engine_maps_success_result_to_report -v`

预期：FAIL，报错包含 `ImportError` 或 `NameError: name 'TradingAgentsDeepResearchEngine' is not defined`。

- [ ] **步骤 3：实现成功映射**

在 `tradingagents_engine.py` 追加：

```python
from money_api.domains.analysis.contracts import (
    AgentView,
    AnalysisReport,
    AnalysisStatus,
    ConfidenceLevel,
    DecisionAction,
    RiskFinding,
)


_ACTION_MAP = {
    "BUY": DecisionAction.BUY,
    "WATCH": DecisionAction.WATCH,
    "HOLD": DecisionAction.WATCH,
    "WAIT": DecisionAction.WAIT,
    "SELL": DecisionAction.SELL,
}


class TradingAgentsDeepResearchEngine:
    def __init__(self, runner: TradingAgentsRunner, trade_date: str | None = None):
        self.runner = runner
        self.trade_date = trade_date

    def analyze(self, task_id: str, context: DataContext) -> AnalysisReport:
        request = TradingAgentsRunRequest.from_context(task_id, context, self.trade_date)
        result = self.runner.run(request)
        diagnostics = list(context.diagnostics) + list(result.diagnostics)
        report_context = DataContext(
            stock=context.stock,
            quote=dict(context.quote),
            technicals=dict(context.technicals),
            fundamentals=dict(context.fundamentals),
            news=list(context.news),
            gaps=list(context.gaps),
            diagnostics=diagnostics,
        )
        if result.ok:
            return AnalysisReport(
                task_id=task_id,
                stock=context.stock,
                status=AnalysisStatus.REPORT_READY,
                action=_ACTION_MAP.get(result.final_decision.upper(), DecisionAction.WATCH),
                confidence=ConfidenceLevel.LOW if context.gaps else ConfidenceLevel.MEDIUM,
                summary=result.summary,
                reasons=["TradingAgents 深度投研引擎已返回结果"],
                risks=[RiskFinding(level="low", message="真实引擎输出仍需人工复核")],
                agent_views=[AgentView(agent=f"TradingAgents {name}", conclusion=report) for name, report in result.agent_reports.items()],
                data_context=report_context,
            )
        return self._failed_report(task_id, context, result, report_context)
```

`_failed_report` 在任务 3 中补齐，任务 2 可以先返回一个最小失败分支或让测试只覆盖成功路径。

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tradingagents_engine.py -v`

预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/domains/analysis/tradingagents_engine.py services/api/tests/test_tradingagents_engine.py
git commit -m "feat: map TradingAgents results to reports" -m "Outline:
- Add TradingAgentsDeepResearchEngine behind the DeepResearchEngine protocol.
- Map fake TradingAgents success results into AnalysisReport.
- Preserve original DataContext data while appending runner diagnostics."
```

---

### 任务 3：失败结果与 diagnostics 映射

**文件：**

- 修改：`services/api/money_api/domains/analysis/tradingagents_engine.py`
- 测试：`services/api/tests/test_tradingagents_engine.py`

- [ ] **步骤 1：编写失败的测试**

追加测试：

```python
class FailingTradingAgentsRunner:
    def run(self, request: TradingAgentsRunRequest) -> TradingAgentsRunResult:
        return TradingAgentsRunResult(
            ok=False,
            source="tradingagents",
            diagnostics=[{"kind": "deep_engine", "source": "tradingagents", "ok": False}],
            error_type="RuntimeError",
            error_message="boom",
        )


def test_tradingagents_engine_maps_failure_to_failed_report() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    context = DataContext(stock=stock, quote={"price": 1688.0})

    report = TradingAgentsDeepResearchEngine(FailingTradingAgentsRunner()).analyze("task-1", context)

    assert report.status.value == "failed"
    assert report.action.value == "watch"
    assert report.confidence.value == "low"
    assert report.risks[0].message == "TradingAgents 执行失败: boom"
    assert report.data_context.diagnostics[-1]["ok"] is False
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tradingagents_engine.py::test_tradingagents_engine_maps_failure_to_failed_report -v`

预期：FAIL，失败分支尚未实现。

- [ ] **步骤 3：实现失败映射**

在 `TradingAgentsDeepResearchEngine` 中补齐：

```python
    def _failed_report(
        self,
        task_id: str,
        context: DataContext,
        result: TradingAgentsRunResult,
        report_context: DataContext,
    ) -> AnalysisReport:
        message = result.error_message or "unknown error"
        return AnalysisReport(
            task_id=task_id,
            stock=context.stock,
            status=AnalysisStatus.FAILED,
            action=DecisionAction.WATCH,
            confidence=ConfidenceLevel.LOW,
            summary="TradingAgents 深度投研引擎执行失败。",
            reasons=["TradingAgents runner 返回失败结果"],
            risks=[RiskFinding(level="high", message=f"TradingAgents 执行失败: {message}")],
            agent_views=[AgentView(agent="TradingAgents", conclusion="真实深度投研未完成")],
            data_context=report_context,
        )
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tradingagents_engine.py -v`

预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/domains/analysis/tradingagents_engine.py services/api/tests/test_tradingagents_engine.py
git commit -m "feat: handle TradingAgents engine failures" -m "Outline:
- Convert failed TradingAgents runner results into serializable failed reports.
- Preserve runner diagnostics on failed reports.
- Cover failure behavior without importing the real TradingAgents package."
```

---

### 任务 4：真实 TradingAgentsGraphRunner 壳

**文件：**

- 创建：`services/api/money_api/integrations/__init__.py`
- 创建：`services/api/money_api/integrations/tradingagents_runner.py`
- 测试：`services/api/tests/test_tradingagents_runner.py`

- [ ] **步骤 1：编写失败的测试**

```python
from money_api.domains.analysis.tradingagents_engine import TradingAgentsRunRequest
from money_api.integrations.tradingagents_runner import TradingAgentsGraphRunner


class FakeGraph:
    def __init__(self, selected_analysts, debug, config):
        self.selected_analysts = selected_analysts
        self.debug = debug
        self.config = config

    def propagate(self, company_name, trade_date):
        return (
            {
                "market_report": "市场报告",
                "news_report": "新闻报告",
                "fundamentals_report": "基本面报告",
                "policy_report": "政策报告",
                "hot_money_report": "游资报告",
                "lockup_report": "解禁报告",
                "final_trade_decision": "WATCH",
            },
            "WATCH",
        )


def test_graph_runner_uses_injected_graph_factory() -> None:
    request = TradingAgentsRunRequest(
        task_id="task-1",
        code="600519",
        name="贵州茅台",
        market="cn",
        trade_date="2026-07-01",
        context_snapshot={},
        diagnostics=[],
    )
    runner = TradingAgentsGraphRunner(graph_factory=FakeGraph, config={"output_language": "Chinese"})

    result = runner.run(request)

    assert result.ok is True
    assert result.source == "tradingagents"
    assert result.final_decision == "WATCH"
    assert result.agent_reports["market"] == "市场报告"


def test_graph_runner_returns_failure_when_graph_raises() -> None:
    class RaisingGraph(FakeGraph):
        def propagate(self, company_name, trade_date):
            raise RuntimeError("boom")

    request = TradingAgentsRunRequest(
        task_id="task-1",
        code="600519",
        name="贵州茅台",
        market="cn",
        trade_date="2026-07-01",
        context_snapshot={},
        diagnostics=[],
    )
    result = TradingAgentsGraphRunner(graph_factory=RaisingGraph).run(request)

    assert result.ok is False
    assert result.error_type == "RuntimeError"
    assert result.error_message == "boom"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tradingagents_runner.py -v`

预期：FAIL，模块不存在。

- [ ] **步骤 3：实现真实 runner 壳**

在 `services/api/money_api/integrations/tradingagents_runner.py` 写入：

```python
"""Optional TradingAgents-astock integration runner."""

from collections.abc import Callable
from typing import Any

from money_api.domains.analysis.tradingagents_engine import TradingAgentsRunRequest, TradingAgentsRunResult


class TradingAgentsGraphRunner:
    def __init__(
        self,
        graph_factory: Callable[..., Any] | None = None,
        selected_analysts: list[str] | None = None,
        config: dict[str, Any] | None = None,
        debug: bool = False,
    ):
        self.graph_factory = graph_factory
        self.selected_analysts = selected_analysts or ["market", "news", "fundamentals", "policy", "hot_money", "lockup"]
        self.config = config or {}
        self.debug = debug

    def run(self, request: TradingAgentsRunRequest) -> TradingAgentsRunResult:
        try:
            graph_factory = self.graph_factory or self._load_graph_factory()
            graph = graph_factory(selected_analysts=self.selected_analysts, debug=self.debug, config=self.config)
            final_state, signal = graph.propagate(request.code, request.trade_date)
            return TradingAgentsRunResult(
                ok=True,
                source="tradingagents",
                final_decision=str(signal or final_state.get("final_trade_decision", "WATCH")),
                summary=str(final_state.get("investment_plan") or final_state.get("final_trade_decision") or signal or "TradingAgents 分析完成"),
                agent_reports={
                    "market": str(final_state.get("market_report", "")),
                    "news": str(final_state.get("news_report", "")),
                    "fundamentals": str(final_state.get("fundamentals_report", "")),
                    "policy": str(final_state.get("policy_report", "")),
                    "hot_money": str(final_state.get("hot_money_report", "")),
                    "lockup": str(final_state.get("lockup_report", "")),
                },
                raw_state=dict(final_state),
                diagnostics=[{"kind": "deep_engine", "source": "tradingagents", "ok": True}],
            )
        except Exception as exc:
            return TradingAgentsRunResult(
                ok=False,
                source="tradingagents",
                diagnostics=[{"kind": "deep_engine", "source": "tradingagents", "ok": False}],
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

    def _load_graph_factory(self) -> Callable[..., Any]:
        from tradingagents.graph.trading_graph import TradingAgentsGraph

        return TradingAgentsGraph
```

创建 `services/api/money_api/integrations/__init__.py`：

```python
"""Optional external integrations for Money_Never_sleep."""
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tradingagents_runner.py -v`

预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/integrations/__init__.py services/api/money_api/integrations/tradingagents_runner.py services/api/tests/test_tradingagents_runner.py
git commit -m "feat: add TradingAgents graph runner" -m "Outline:
- Add an optional runner wrapper around TradingAgentsGraph.
- Support injected graph factories for deterministic tests.
- Convert graph success and failure paths into TradingAgentsRunResult."
```

---

### 任务 5：API 可选工厂与配置入口

**文件：**

- 修改：`services/api/money_api/api/v1/router.py`
- 修改：`services/api/money_api/core/config.py`
- 修改：`.env.example`
- 测试：`services/api/tests/test_analysis_api.py`

- [ ] **步骤 1：编写失败的测试**

在 `services/api/tests/test_analysis_api.py` 追加：

```python
from money_api.domains.analysis.tradingagents_engine import FakeTradingAgentsRunner


def test_tradingagents_service_factory_accepts_runner() -> None:
    service = build_tradingagents_analysis_service(runner=FakeTradingAgentsRunner())
    payload = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议").to_dict()

    assert payload["status"] == "report_ready"
    assert payload["data_diagnostics"][-1]["source"] == "fake-tradingagents"
```

同时补充 import：

```python
from money_api.api.v1.router import build_default_analysis_service, build_tencent_quote_analysis_service, build_tradingagents_analysis_service
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_analysis_api.py::test_tradingagents_service_factory_accepts_runner -v`

预期：FAIL，`build_tradingagents_analysis_service` 尚不存在。

- [ ] **步骤 3：实现配置与工厂**

在 `core/config.py` 中扩展：

```python
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    env: str = os.getenv("MONEY_ENV", "development")
    api_host: str = os.getenv("MONEY_API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("MONEY_API_PORT", "8000"))
    tradingagents_astock_path: str = os.getenv("TRADINGAGENTS_ASTOCK_PATH", "../TradingAgents-astock")
    tradingagents_results_dir: str = os.getenv("TRADINGAGENTS_RESULTS_DIR", "data/cache/tradingagents/results")
    tradingagents_cache_dir: str = os.getenv("TRADINGAGENTS_CACHE_DIR", "data/cache/tradingagents/cache")
```

在 `.env.example` 追加：

```dotenv
# Optional TradingAgents deep engine integration. Keep disabled unless explicitly running stage 3 smoke.
MNS_RUN_TRADINGAGENTS_SMOKE=0
TRADINGAGENTS_RESULTS_DIR=data/cache/tradingagents/results
TRADINGAGENTS_CACHE_DIR=data/cache/tradingagents/cache
```

在 `router.py` 中新增：

```python
from money_api.domains.analysis.tradingagents_engine import TradingAgentsDeepResearchEngine, TradingAgentsRunner


def build_tradingagents_analysis_service(runner: TradingAgentsRunner | None = None) -> AnalysisService:
    deep_engine = TradingAgentsDeepResearchEngine(runner or FakeTradingAgentsRunner())
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
        deep_engine=deep_engine,
    )
```

确保也 import `FakeTradingAgentsRunner`，或者在默认 runner 分支创建真实 runner 前先保持 fake。

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_analysis_api.py services/api/tests/test_tradingagents_engine.py -v`

预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/api/v1/router.py services/api/money_api/core/config.py .env.example services/api/tests/test_analysis_api.py
git commit -m "feat: add TradingAgents analysis service factory" -m "Outline:
- Add opt-in TradingAgents analysis service factory without changing the default API path.
- Add non-secret TradingAgents configuration defaults.
- Verify API-level factory behavior with the fake runner."
```

---

### 任务 6：opt-in TradingAgents smoke

**文件：**

- 创建：`services/api/tests/test_tradingagents_smoke.py`
- 修改：`pyproject.toml`
- 测试：`services/api/tests/test_tradingagents_smoke.py`

- [ ] **步骤 1：编写 smoke 测试**

```python
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
```

- [ ] **步骤 2：注册 pytest marker**

在 `pyproject.toml` 中将 markers 改为：

```toml
markers = [
  "network: tests requiring external network access",
  "external_engine: tests requiring optional external analysis engines",
]
```

保留已有 `network` marker。

- [ ] **步骤 3：运行 smoke 文件验证默认 skip**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tradingagents_smoke.py -v`

预期：PASS，结果为 `1 skipped`。

- [ ] **步骤 4：Commit**

```bash
git add services/api/tests/test_tradingagents_smoke.py pyproject.toml
git commit -m "test: add optional TradingAgents smoke" -m "Outline:
- Add an opt-in smoke test for the optional TradingAgents engine path.
- Register an external_engine pytest marker.
- Keep default test runs independent of TradingAgents and LLM credentials."
```

---

### 任务 7：文档与最终验证

**文件：**

- 修改：`README.md`
- 修改：`docs/stages.md`

- [ ] **步骤 1：更新 README 当前实现切片**

将当前实现切片中的阶段描述更新为：

```markdown
当前阶段正在接入 TradingAgents 深度引擎：默认 API 仍保持 mock deep engine，阶段 3 将通过可选 adapter/runner 让 TradingAgents-astock 成为显式启用的真实深度投研后端。
```

保留 README 中文默认与英文选项说明。

- [ ] **步骤 2：更新 stages 状态**

在 `docs/stages.md` 中：

- 将阶段 3 状态改为 `已完成`。
- 当前阶段结论改为阶段 3 完成内容。
- 记录默认离线测试结果。
- 记录 smoke 命令：

```bash
MNS_RUN_TRADINGAGENTS_SMOKE=1 PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tradingagents_smoke.py -v
```

- 下一阶段建议改为阶段 4“报告、历史与复盘”。

- [ ] **步骤 3：运行最终验证**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -v`

预期：PASS，external smoke 默认 skip。

运行：`git diff --check README.md docs/stages.md docs/superpowers/plans/2026-07-01-stage-3-tradingagents-engine.md docs/superpowers/specs/2026-07-01-stage-3-tradingagents-engine-design.md`

预期：退出码 0，无输出。

- [ ] **步骤 4：Commit**

```bash
git add README.md docs/stages.md
git commit -m "docs: document stage 3 engine integration" -m "Outline:
- Update README with the TradingAgents adapter direction.
- Mark stage 3 complete in the living stage roadmap.
- Record validation and the optional TradingAgents smoke command."
```

---

## 计划自检结果

### 规格覆盖度

- Adapter + runner 协议：任务 1、2 覆盖。
- Fake runner 离线测试：任务 1、2、5 覆盖。
- 失败降级与 diagnostics：任务 3 覆盖。
- 真实 TradingAgentsGraph runner 壳：任务 4 覆盖。
- API opt-in 工厂与默认 mock 保持不变：任务 5 覆盖。
- opt-in smoke：任务 6 覆盖。
- README 与阶段活文档：任务 7 覆盖。
- Web/桌面、持久化、队列、成本看板：明确不属于本计划。

### 红旗词扫描

计划正文不使用未完成红旗表达；每个实现步骤都包含目标文件、示例测试、实现方向、命令和提交大纲。

### 类型一致性

- `TradingAgentsRunRequest`、`TradingAgentsRunResult`、`TradingAgentsRunner` 在任务 1 定义，任务 2-6 使用同一路径 `money_api.domains.analysis.tradingagents_engine`。
- `TradingAgentsDeepResearchEngine` 在任务 2 定义，任务 3 和任务 5 复用同一签名。
- `TradingAgentsGraphRunner` 在任务 4 定义，任务 6 复用同一路径 `money_api.integrations.tradingagents_runner`。
