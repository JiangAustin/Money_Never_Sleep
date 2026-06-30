# 单股深度分析平台骨架实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 构建 Money_Never_sleep 第一阶段的后端平台骨架，让单股深度分析可以通过稳定领域契约、离线数据上下文、Agent 适配器和 API 入口完成可测试 dry run。

**架构：** 本计划只覆盖后端/API 垂直切片，不实现 Web 和桌面 UI。实现围绕 `money_api.domains.analysis` 和 `money_api.domains.market_data` 建立领域模型，API 层只调用分析服务，不绑定具体 AI 框架；深度投研先用 mock engine 固定契约，再在独立计划中接入 TradingAgents-astock。

**技术栈：** Python 3.10+、dataclasses、Enum、Protocol、pytest、当前 `services/api/money_api` 包结构。

---

## 范围切分

设计规格包含 Web、桌面、数据源、Agent 深度引擎、报告、风控和验证。为保证计划可独立交付，本计划只实现第一条后端骨架切片：

- 股票标识解析。
- 分析领域契约。
- 离线数据上下文 builder。
- Quick Agent 路由和 mock deep engine。
- 分析任务服务。
- Python API 函数入口。

Web 工作台、桌面端、真实数据 provider、TradingAgents-astock 集成、持久化数据库和回测分别进入单独计划。

## 文件结构

- 创建：`services/api/money_api/domains/analysis/contracts.py`  
  定义分析状态、结论枚举、股票身份、数据上下文、风险项、Agent 观点、报告、任务快照。
- 创建：`services/api/money_api/domains/market_data/resolver.py`  
  解析 A 股代码、交易所前后缀和注入式中文名称映射。
- 创建：`services/api/money_api/domains/analysis/context_builder.py`  
  从 provider 读取离线上下文，显式记录数据缺口。
- 创建：`services/api/money_api/domains/analysis/agent_engine.py`  
  定义 Agent 引擎协议、Quick 路由和 mock deep research engine。
- 创建：`services/api/money_api/domains/analysis/service.py`  
  编排一次单股分析 dry run，管理状态流转并生成报告。
- 修改：`services/api/money_api/api/v1/router.py`  
  暴露 Python 函数级 API：健康检查、创建单股分析、查询任务。
- 修改：`services/api/money_api/main.py`  
  保留 `health()`，增加薄入口函数转发到 v1 router。
- 创建：`services/api/tests/test_analysis_contracts.py`
- 创建：`services/api/tests/test_stock_resolver.py`
- 创建：`services/api/tests/test_context_builder.py`
- 创建：`services/api/tests/test_agent_engine.py`
- 创建：`services/api/tests/test_analysis_service.py`
- 创建：`services/api/tests/test_analysis_api.py`

---

### 任务 1：分析领域契约

**文件：**
- 创建：`services/api/money_api/domains/analysis/contracts.py`
- 测试：`services/api/tests/test_analysis_contracts.py`

- [ ] **步骤 1：编写失败的测试**

```python
from money_api.domains.analysis.contracts import (
    AgentView,
    AnalysisReport,
    AnalysisStatus,
    ConfidenceLevel,
    DataContext,
    DecisionAction,
    RiskFinding,
    StockIdentity,
)


def test_report_to_dict_contains_required_sections() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台", market="cn")
    context = DataContext(
        stock=stock,
        quote={"price": 1688.0},
        technicals={"ma5": 1660.0},
        fundamentals={"pe_ttm": 28.5},
        news=[{"title": "业绩稳定"}],
        gaps=["资金流不可用"],
    )
    report = AnalysisReport(
        task_id="task-1",
        stock=stock,
        status=AnalysisStatus.REPORT_READY,
        action=DecisionAction.WATCH,
        confidence=ConfidenceLevel.MEDIUM,
        summary="等待回踩确认",
        reasons=["趋势仍在"],
        risks=[RiskFinding(level="medium", message="短期偏离 MA5")],
        agent_views=[AgentView(agent="Market Analyst", conclusion="趋势偏强")],
        data_context=context,
    )

    payload = report.to_dict()

    assert payload["stock"] == {"code": "600519", "name": "贵州茅台", "market": "cn"}
    assert payload["status"] == "report_ready"
    assert payload["action"] == "watch"
    assert payload["confidence"] == "medium"
    assert payload["data_gaps"] == ["资金流不可用"]
    assert payload["risks"] == [{"level": "medium", "message": "短期偏离 MA5"}]
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api pytest services/api/tests/test_analysis_contracts.py -v`  
预期：FAIL，报错包含 `ModuleNotFoundError: No module named 'money_api.domains.analysis.contracts'`。

- [ ] **步骤 3：编写最少实现代码**

创建 `services/api/money_api/domains/analysis/contracts.py`：

```python
"""Analysis domain contracts for Money_Never_sleep."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AnalysisStatus(str, Enum):
    QUEUED = "queued"
    COLLECTING_DATA = "collecting_data"
    QUICK_SCREENING = "quick_screening"
    DEEP_ANALYSIS = "deep_analysis"
    RISK_REVIEW = "risk_review"
    REPORT_READY = "report_ready"
    FAILED = "failed"


class DecisionAction(str, Enum):
    BUY = "buy"
    WATCH = "watch"
    SELL = "sell"
    WAIT = "wait"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class StockIdentity:
    code: str
    name: str
    market: str = "cn"

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "name": self.name, "market": self.market}


@dataclass(frozen=True)
class RiskFinding:
    level: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"level": self.level, "message": self.message}


@dataclass(frozen=True)
class AgentView:
    agent: str
    conclusion: str

    def to_dict(self) -> dict[str, str]:
        return {"agent": self.agent, "conclusion": self.conclusion}


@dataclass(frozen=True)
class DataContext:
    stock: StockIdentity
    quote: dict[str, Any] = field(default_factory=dict)
    technicals: dict[str, Any] = field(default_factory=dict)
    fundamentals: dict[str, Any] = field(default_factory=dict)
    news: list[dict[str, Any]] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AnalysisReport:
    task_id: str
    stock: StockIdentity
    status: AnalysisStatus
    action: DecisionAction
    confidence: ConfidenceLevel
    summary: str
    reasons: list[str]
    risks: list[RiskFinding]
    agent_views: list[AgentView]
    data_context: DataContext

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "stock": self.stock.to_dict(),
            "status": self.status.value,
            "action": self.action.value,
            "confidence": self.confidence.value,
            "summary": self.summary,
            "reasons": list(self.reasons),
            "risks": [risk.to_dict() for risk in self.risks],
            "agent_views": [view.to_dict() for view in self.agent_views],
            "data_gaps": list(self.data_context.gaps),
        }
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api pytest services/api/tests/test_analysis_contracts.py -v`  
预期：PASS，输出包含 `1 passed`。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/domains/analysis/contracts.py services/api/tests/test_analysis_contracts.py
git commit -m "feat: add analysis domain contracts" -m "Outline:
- Define analysis status, decision, confidence, and report contracts.
- Add serializable stock, risk, agent view, and data context models.
- Cover required report sections with focused unit tests."
```

---

### 任务 2：A 股股票解析器

**文件：**
- 创建：`services/api/money_api/domains/market_data/resolver.py`
- 测试：`services/api/tests/test_stock_resolver.py`

- [ ] **步骤 1：编写失败的测试**

```python
import pytest

from money_api.domains.market_data.resolver import StockResolver, normalize_stock_code


def test_normalize_a_share_code_formats() -> None:
    assert normalize_stock_code("600519") == "600519"
    assert normalize_stock_code("SH600519") == "600519"
    assert normalize_stock_code("600519.SH") == "600519"
    assert normalize_stock_code("sz000001") == "000001"


def test_resolve_chinese_name_from_injected_map() -> None:
    resolver = StockResolver(name_map={"贵州茅台": "600519"})

    stock = resolver.resolve("贵州茅台")

    assert stock.code == "600519"
    assert stock.name == "贵州茅台"
    assert stock.market == "cn"


def test_reject_unknown_symbol() -> None:
    resolver = StockResolver(name_map={})


    with pytest.raises(ValueError, match="无法解析股票"):
        resolver.resolve("不存在股票")
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api pytest services/api/tests/test_stock_resolver.py -v`  
预期：FAIL，报错包含 `ModuleNotFoundError: No module named 'money_api.domains.market_data.resolver'`。

- [ ] **步骤 3：编写最少实现代码**

创建 `services/api/money_api/domains/market_data/resolver.py`：

```python
"""Stock symbol resolver for the first Money_Never_sleep slice."""

import re

from money_api.domains.analysis.contracts import StockIdentity


def normalize_stock_code(raw_symbol: str) -> str:
    symbol = raw_symbol.strip().upper()
    for suffix in (".SH", ".SZ", ".BJ"):
        if symbol.endswith(suffix):
            symbol = symbol[: -len(suffix)]
            break
    for prefix in ("SH", "SZ", "BJ"):
        if symbol.startswith(prefix):
            symbol = symbol[len(prefix) :]
            break
    if re.fullmatch(r"\d{6}", symbol):
        return symbol
    raise ValueError(f"无法解析股票: {raw_symbol}")


class StockResolver:
    def __init__(self, name_map: dict[str, str] | None = None):
        self.name_map = name_map or {}

    def resolve(self, raw_symbol: str) -> StockIdentity:
        cleaned = raw_symbol.strip()
        if not cleaned:
            raise ValueError("无法解析股票: 输入为空")
        if cleaned in self.name_map:
            return StockIdentity(code=self.name_map[cleaned], name=cleaned, market="cn")
        code = normalize_stock_code(cleaned)
        return StockIdentity(code=code, name=code, market="cn")
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api pytest services/api/tests/test_stock_resolver.py -v`  
预期：PASS，输出包含 `3 passed`。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/domains/market_data/resolver.py services/api/tests/test_stock_resolver.py
git commit -m "feat: add stock resolver" -m "Outline:
- Normalize common A-share code formats.
- Resolve injected Chinese stock names for offline tests.
- Reject unknown or empty stock inputs with explicit errors."
```

---

### 任务 3：数据上下文 Builder

**文件：**
- 创建：`services/api/money_api/domains/analysis/context_builder.py`
- 测试：`services/api/tests/test_context_builder.py`

- [ ] **步骤 1：编写失败的测试**

```python
from money_api.domains.analysis.context_builder import DataContextBuilder, StaticMarketDataProvider
from money_api.domains.analysis.contracts import StockIdentity


def test_build_context_collects_available_data() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    provider = StaticMarketDataProvider(
        quote={"price": 1688.0},
        technicals={"ma5": 1660.0},
        fundamentals={"pe_ttm": 28.5},
        news=[{"title": "业绩稳定"}],
    )

    context = DataContextBuilder(provider).build(stock)

    assert context.stock == stock
    assert context.quote["price"] == 1688.0
    assert context.technicals["ma5"] == 1660.0
    assert context.fundamentals["pe_ttm"] == 28.5
    assert context.news == [{"title": "业绩稳定"}]
    assert context.gaps == []


def test_build_context_records_data_gaps() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    provider = StaticMarketDataProvider(quote={"price": 1688.0})

    context = DataContextBuilder(provider).build(stock)

    assert context.gaps == ["technicals", "fundamentals", "news"]
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api pytest services/api/tests/test_context_builder.py -v`  
预期：FAIL，报错包含 `ModuleNotFoundError: No module named 'money_api.domains.analysis.context_builder'`。

- [ ] **步骤 3：编写最少实现代码**

创建 `services/api/money_api/domains/analysis/context_builder.py`：

```python
"""Build normalized data context for analysis runs."""

from dataclasses import dataclass, field
from typing import Any, Protocol

from money_api.domains.analysis.contracts import DataContext, StockIdentity


class MarketDataProvider(Protocol):
    def get_quote(self, stock: StockIdentity) -> dict[str, Any]: ...
    def get_technicals(self, stock: StockIdentity) -> dict[str, Any]: ...
    def get_fundamentals(self, stock: StockIdentity) -> dict[str, Any]: ...
    def get_news(self, stock: StockIdentity) -> list[dict[str, Any]]: ...


@dataclass
class StaticMarketDataProvider:
    quote: dict[str, Any] = field(default_factory=dict)
    technicals: dict[str, Any] = field(default_factory=dict)
    fundamentals: dict[str, Any] = field(default_factory=dict)
    news: list[dict[str, Any]] = field(default_factory=list)

    def get_quote(self, stock: StockIdentity) -> dict[str, Any]:
        return dict(self.quote)

    def get_technicals(self, stock: StockIdentity) -> dict[str, Any]:
        return dict(self.technicals)

    def get_fundamentals(self, stock: StockIdentity) -> dict[str, Any]:
        return dict(self.fundamentals)

    def get_news(self, stock: StockIdentity) -> list[dict[str, Any]]:
        return list(self.news)


class DataContextBuilder:
    def __init__(self, provider: MarketDataProvider):
        self.provider = provider

    def build(self, stock: StockIdentity) -> DataContext:
        quote = self.provider.get_quote(stock)
        technicals = self.provider.get_technicals(stock)
        fundamentals = self.provider.get_fundamentals(stock)
        news = self.provider.get_news(stock)
        gaps = []
        if not quote:
            gaps.append("quote")
        if not technicals:
            gaps.append("technicals")
        if not fundamentals:
            gaps.append("fundamentals")
        if not news:
            gaps.append("news")
        return DataContext(
            stock=stock,
            quote=quote,
            technicals=technicals,
            fundamentals=fundamentals,
            news=news,
            gaps=gaps,
        )
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api pytest services/api/tests/test_context_builder.py -v`  
预期：PASS，输出包含 `2 passed`。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/domains/analysis/context_builder.py services/api/tests/test_context_builder.py
git commit -m "feat: build analysis data context" -m "Outline:
- Add a provider protocol for analysis inputs.
- Provide an offline static provider for deterministic tests.
- Record explicit data gaps in every context."
```

---

### 任务 4：Agent 引擎适配器

**文件：**
- 创建：`services/api/money_api/domains/analysis/agent_engine.py`
- 测试：`services/api/tests/test_agent_engine.py`

- [ ] **步骤 1：编写失败的测试**

```python
from money_api.domains.analysis.agent_engine import MockDeepResearchEngine, QuickAgentRouter
from money_api.domains.analysis.contracts import DataContext, StockIdentity


def test_quick_router_detects_deep_analysis_request() -> None:
    router = QuickAgentRouter()

    assert router.needs_deep_analysis("请全面分析贵州茅台并给出投资建议") is True
    assert router.needs_deep_analysis("贵州茅台现在多少钱") is False


def test_mock_engine_generates_report_with_low_confidence_when_gaps_exist() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    context = DataContext(stock=stock, quote={"price": 1688.0}, gaps=["news"])

    report = MockDeepResearchEngine().analyze("task-1", context)

    assert report.task_id == "task-1"
    assert report.stock == stock
    assert report.confidence.value == "low"
    assert report.action.value == "watch"
    assert report.agent_views[0].agent == "Mock Research Engine"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api pytest services/api/tests/test_agent_engine.py -v`  
预期：FAIL，报错包含 `ModuleNotFoundError: No module named 'money_api.domains.analysis.agent_engine'`。

- [ ] **步骤 3：编写最少实现代码**

创建 `services/api/money_api/domains/analysis/agent_engine.py`：

```python
"""Agent engine abstractions for analysis orchestration."""

from typing import Protocol

from money_api.domains.analysis.contracts import (
    AgentView,
    AnalysisReport,
    AnalysisStatus,
    ConfidenceLevel,
    DataContext,
    DecisionAction,
    RiskFinding,
)


class DeepResearchEngine(Protocol):
    def analyze(self, task_id: str, context: DataContext) -> AnalysisReport: ...


class QuickAgentRouter:
    deep_keywords = ("全面分析", "深度分析", "投资建议", "操作建议", "风险评估")

    def needs_deep_analysis(self, message: str) -> bool:
        return any(keyword in message for keyword in self.deep_keywords)


class MockDeepResearchEngine:
    def analyze(self, task_id: str, context: DataContext) -> AnalysisReport:
        confidence = ConfidenceLevel.LOW if context.gaps else ConfidenceLevel.MEDIUM
        risks = [RiskFinding(level="medium", message=f"数据缺口: {gap}") for gap in context.gaps]
        if not risks:
            risks = [RiskFinding(level="low", message="当前为 mock 分析，需接入真实投研引擎验证")]
        return AnalysisReport(
            task_id=task_id,
            stock=context.stock,
            status=AnalysisStatus.REPORT_READY,
            action=DecisionAction.WATCH,
            confidence=confidence,
            summary="当前为平台骨架 dry run，结论仅用于验证分析契约。",
            reasons=["已完成数据上下文构建", "已通过 Agent 引擎适配器生成报告"],
            risks=risks,
            agent_views=[AgentView(agent="Mock Research Engine", conclusion="等待真实深度投研引擎接入")],
            data_context=context,
        )
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api pytest services/api/tests/test_agent_engine.py -v`  
预期：PASS，输出包含 `2 passed`。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/domains/analysis/agent_engine.py services/api/tests/test_agent_engine.py
git commit -m "feat: add analysis agent engine adapter" -m "Outline:
- Define the deep research engine protocol.
- Add quick routing for deep-analysis requests.
- Provide a mock engine that preserves report and risk contracts."
```

---

### 任务 5：分析任务服务

**文件：**
- 创建：`services/api/money_api/domains/analysis/service.py`
- 测试：`services/api/tests/test_analysis_service.py`

- [ ] **步骤 1：编写失败的测试**

```python
from money_api.domains.analysis.agent_engine import MockDeepResearchEngine, QuickAgentRouter
from money_api.domains.analysis.context_builder import DataContextBuilder, StaticMarketDataProvider
from money_api.domains.analysis.service import AnalysisService
from money_api.domains.market_data.resolver import StockResolver


def build_service() -> AnalysisService:
    return AnalysisService(
        resolver=StockResolver(name_map={"贵州茅台": "600519"}),
        context_builder=DataContextBuilder(
            StaticMarketDataProvider(
                quote={"price": 1688.0},
                technicals={"ma5": 1660.0},
                fundamentals={"pe_ttm": 28.5},
                news=[{"title": "业绩稳定"}],
            )
        ),
        quick_router=QuickAgentRouter(),
        deep_engine=MockDeepResearchEngine(),
    )


def test_create_single_stock_analysis_returns_report() -> None:
    service = build_service()

    report = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议")

    assert report.stock.code == "600519"
    assert report.status.value == "report_ready"
    assert report.summary
    assert service.get_report(report.task_id) == report


def test_lightweight_question_uses_quick_summary() -> None:
    service = build_service()

    report = service.create_single_stock_analysis("600519", "现在多少钱")

    assert report.action.value == "watch"
    assert report.agent_views[0].agent == "Quick Agent"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api pytest services/api/tests/test_analysis_service.py -v`  
预期：FAIL，报错包含 `ModuleNotFoundError: No module named 'money_api.domains.analysis.service'`。

- [ ] **步骤 3：编写最少实现代码**

创建 `services/api/money_api/domains/analysis/service.py`：

```python
"""Application service for single-stock analysis dry runs."""

from uuid import uuid4

from money_api.domains.analysis.agent_engine import DeepResearchEngine, QuickAgentRouter
from money_api.domains.analysis.context_builder import DataContextBuilder
from money_api.domains.analysis.contracts import (
    AgentView,
    AnalysisReport,
    AnalysisStatus,
    ConfidenceLevel,
    DecisionAction,
    RiskFinding,
)
from money_api.domains.market_data.resolver import StockResolver


class AnalysisService:
    def __init__(
        self,
        resolver: StockResolver,
        context_builder: DataContextBuilder,
        quick_router: QuickAgentRouter,
        deep_engine: DeepResearchEngine,
    ):
        self.resolver = resolver
        self.context_builder = context_builder
        self.quick_router = quick_router
        self.deep_engine = deep_engine
        self._reports: dict[str, AnalysisReport] = {}

    def create_single_stock_analysis(self, symbol: str, message: str) -> AnalysisReport:
        task_id = f"analysis-{uuid4().hex}"
        stock = self.resolver.resolve(symbol)
        context = self.context_builder.build(stock)
        if self.quick_router.needs_deep_analysis(message):
            report = self.deep_engine.analyze(task_id, context)
        else:
            report = AnalysisReport(
                task_id=task_id,
                stock=stock,
                status=AnalysisStatus.REPORT_READY,
                action=DecisionAction.WATCH,
                confidence=ConfidenceLevel.LOW if context.gaps else ConfidenceLevel.MEDIUM,
                summary="轻量查询已完成，未触发完整深度投研流程。",
                reasons=["问题未命中深度分析关键词", "已复用统一数据上下文"],
                risks=[RiskFinding(level="low", message="轻量结论不构成完整投资建议")],
                agent_views=[AgentView(agent="Quick Agent", conclusion="返回轻量分析摘要")],
                data_context=context,
            )
        self._reports[report.task_id] = report
        return report

    def get_report(self, task_id: str) -> AnalysisReport | None:
        return self._reports.get(task_id)
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api pytest services/api/tests/test_analysis_service.py -v`  
预期：PASS，输出包含 `2 passed`。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/domains/analysis/service.py services/api/tests/test_analysis_service.py
git commit -m "feat: orchestrate single stock analysis" -m "Outline:
- Resolve stock input into a normalized identity.
- Build data context and route quick versus deep analysis.
- Store reports in an in-memory service for the first dry-run slice."
```

---

### 任务 6：Python API 入口

**文件：**
- 修改：`services/api/money_api/api/v1/router.py`
- 修改：`services/api/money_api/main.py`
- 测试：`services/api/tests/test_analysis_api.py`
- 回归：`services/api/tests/test_health.py`

- [ ] **步骤 1：编写失败的测试**

```python
from money_api.main import analyze_stock, get_analysis_report, health


def test_analyze_stock_api_returns_serialized_report() -> None:
    payload = analyze_stock("贵州茅台", "请全面分析并给出投资建议")

    assert payload["stock"]["code"] == "600519"
    assert payload["status"] == "report_ready"
    assert payload["summary"]
    assert payload["agent_views"]

    loaded = get_analysis_report(payload["task_id"])
    assert loaded == payload


def test_health_api_still_returns_original_payload() -> None:
    assert health() == {"status": "ok", "service": "money-never-sleep-api"}
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api pytest services/api/tests/test_analysis_api.py services/api/tests/test_health.py -v`  
预期：FAIL，报错包含 `ImportError: cannot import name 'analyze_stock' from 'money_api.main'`。

- [ ] **步骤 3：编写最少实现代码**

修改 `services/api/money_api/api/v1/router.py`：

```python
"""Version 1 route functions for the Money_Never_sleep API."""

from money_api.domains.analysis.agent_engine import MockDeepResearchEngine, QuickAgentRouter
from money_api.domains.analysis.context_builder import DataContextBuilder, StaticMarketDataProvider
from money_api.domains.analysis.service import AnalysisService
from money_api.domains.market_data.resolver import StockResolver
from money_api.main import health


def build_default_analysis_service() -> AnalysisService:
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
        deep_engine=MockDeepResearchEngine(),
    )


_analysis_service = build_default_analysis_service()


def analyze_stock(symbol: str, message: str) -> dict[str, object]:
    return _analysis_service.create_single_stock_analysis(symbol, message).to_dict()


def get_analysis_report(task_id: str) -> dict[str, object] | None:
    report = _analysis_service.get_report(task_id)
    return report.to_dict() if report is not None else None


def routes() -> dict[str, object]:
    return {"health": health()}
```

修改 `services/api/money_api/main.py`，避免循环导入：

```python
"""Minimal API application boundary for the Money_Never_sleep workspace."""


def health() -> dict[str, str]:
    """Return a minimal health payload for early scaffolding checks."""
    return {"status": "ok", "service": "money-never-sleep-api"}


def analyze_stock(symbol: str, message: str) -> dict[str, object]:
    from money_api.api.v1.router import analyze_stock as analyze_stock_v1

    return analyze_stock_v1(symbol, message)


def get_analysis_report(task_id: str) -> dict[str, object] | None:
    from money_api.api.v1.router import get_analysis_report as get_analysis_report_v1

    return get_analysis_report_v1(task_id)


if __name__ == "__main__":
    print(health())
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api pytest services/api/tests/test_analysis_api.py services/api/tests/test_health.py -v`  
预期：PASS，输出包含 `3 passed`。

- [ ] **步骤 5：运行本切片全部测试**

运行：`PYTHONPATH=services/api pytest services/api/tests -v`  
预期：PASS，所有现有 API 测试通过。

- [ ] **步骤 6：Commit**

```bash
git add services/api/money_api/api/v1/router.py services/api/money_api/main.py services/api/tests/test_analysis_api.py
git commit -m "feat: expose single stock analysis API" -m "Outline:
- Add Python-level API entrypoints for single-stock analysis.
- Wire the default offline analysis service through v1 router functions.
- Preserve the original health contract and cover it with regression tests."
```

---

### 任务 7：文档和最终验证

**文件：**
- 修改：`README.md`
- 修改：`docs/roadmap.md`

- [ ] **步骤 1：更新 README 的第一阶段说明**

在 `README.md` 的 `First Milestone` 段落之后追加：

```markdown

## Current Planning Slice

The first implementation slice is the backend contract for a single-stock deep analysis loop:

1. Resolve an A-share symbol or Chinese stock name.
2. Build a normalized data context with explicit data gaps.
3. Route quick questions separately from deep analysis requests.
4. Generate a structured dry-run report through an Agent engine adapter.
5. Expose Python-level API functions for tests and early integration.
```

- [ ] **步骤 2：更新 roadmap 的实现顺序**

将 `docs/roadmap.md` 的 `Step 2: First Vertical Slice` 替换为：

```markdown
## Step 2: First Vertical Slice

- Build the backend contract for a single-stock deep analysis loop.
- Keep the first slice deterministic with offline fixtures and a mock deep research engine.
- Add TradingAgents-astock integration only after the platform contract and report schema are tested.
```

- [ ] **步骤 3：运行文档格式检查**

运行：`git diff --check README.md docs/roadmap.md docs/superpowers/plans/2026-07-01-single-stock-analysis-platform.md`  
预期：命令退出码为 `0` 且无输出，表示没有尾随空格或补丁格式问题。

- [ ] **步骤 4：运行全部 API 测试**

运行：`PYTHONPATH=services/api pytest services/api/tests -v`  
预期：PASS，所有 API 测试通过。

- [ ] **步骤 5：Commit**

```bash
git add README.md docs/roadmap.md
git commit -m "docs: describe first analysis slice" -m "Outline:
- Document the first backend slice in README.
- Update the roadmap to prioritize deterministic platform contracts.
- Keep TradingAgents integration behind tested adapter boundaries."
```

---

## 计划自检结果

### 规格覆盖度

- 平台骨架：任务 1、5、6 覆盖。
- 股票解析：任务 2 覆盖。
- 数据上下文和数据缺口：任务 3 覆盖。
- Quick Agent 与 Deep Research Engine 分离：任务 4、5 覆盖。
- 报告结构、风险、置信度：任务 1、4、5 覆盖。
- API 入口：任务 6 覆盖。
- 文档同步：任务 7 覆盖。
- Web、桌面、真实数据源、TradingAgents 集成、持久化和回测：已在范围切分中明确为独立计划，不属于本计划交付内容。

### 占位符扫描

计划正文不使用占位符红旗表达；每个代码变更步骤都提供了具体文件、代码片段、命令和预期输出。

### 类型一致性

- `StockIdentity`、`DataContext`、`AnalysisReport` 在任务 1 定义，任务 2-6 复用相同导入路径。
- `QuickAgentRouter.needs_deep_analysis()` 在任务 4 定义，任务 5 复用相同方法名。
- `MockDeepResearchEngine.analyze(task_id, context)` 在任务 4 定义，任务 5 通过 `DeepResearchEngine` 协议使用相同签名。
- `AnalysisService.create_single_stock_analysis(symbol, message)` 在任务 5 定义，任务 6 API 入口复用相同签名。