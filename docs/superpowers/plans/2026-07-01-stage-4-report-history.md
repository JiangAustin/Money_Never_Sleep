# 阶段 4 报告、历史与复盘实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 建立报告历史存储边界，让单股分析报告、数据上下文和 diagnostics 可以保存、读取和列出最近记录。

**架构：** 先扩展 `DataContext` / `AnalysisReport` 的 round-trip 序列化，再新增 report repository 协议、内存实现和 JSON 文件实现。`AnalysisService` 改为依赖 repository，API 层新增 `list_analysis_reports()`，默认服务使用本地 JSON repository。

**技术栈：** Python 3.10+、dataclasses、Protocol、pathlib、json、pytest、当前 `services/api/money_api` 包结构。

---

## 范围切分

本计划只覆盖阶段 4 的最小报告历史能力：

- `DataContext` / `AnalysisReport` 可序列化、可恢复。
- 报告记录契约和 repository 协议。
- 内存 repository 和 JSON 文件 repository。
- `AnalysisService` 保存、读取、列出报告。
- Python API 新增历史列表函数。
- README 和阶段文档更新。

不实现：Web 页面、桌面 UI、SQLite 迁移、全文搜索、删除/收藏/标签、追问链路。

## 文件结构

- 修改：`services/api/money_api/domains/analysis/contracts.py`
  增加 `DataContext.to_dict()` / `from_dict()` 和 `AnalysisReport.from_dict()`，并让 `AnalysisReport.to_dict()` 输出完整 `data_context`。
- 创建：`services/api/money_api/domains/analysis/report_repository.py`
  定义 `AnalysisReportRecord`、`AnalysisReportRepository`、`InMemoryAnalysisReportRepository`、`JsonFileAnalysisReportRepository`。
- 修改：`services/api/money_api/domains/analysis/service.py`
  依赖 repository 保存、读取和列出报告。
- 修改：`services/api/money_api/api/v1/router.py`
  默认服务使用 JSON repository，新增 `list_analysis_reports(limit=20)`。
- 修改：`services/api/money_api/main.py`
  暴露 `list_analysis_reports()`。
- 修改：`services/api/money_api/core/config.py`
  增加 `analysis_reports_dir` 配置。
- 修改：`.env.example`
  增加 `MONEY_REPORTS_DIR` 示例。
- 修改：`services/api/tests/test_analysis_contracts.py`
- 创建：`services/api/tests/test_report_repository.py`
- 修改：`services/api/tests/test_analysis_service.py`
- 修改：`services/api/tests/test_analysis_api.py`
- 修改：`README.md`
- 修改：`docs/stages.md`

---

### 任务 1：报告与数据上下文 round-trip 契约

**文件：**

- 修改：`services/api/money_api/domains/analysis/contracts.py`
- 修改：`services/api/tests/test_analysis_contracts.py`

- [ ] **步骤 1：编写失败的测试**

在 `services/api/tests/test_analysis_contracts.py` 追加：

```python
def test_data_context_round_trip_preserves_payloads() -> None:
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

    restored = DataContext.from_dict(context.to_dict())

    assert restored == context


def test_analysis_report_round_trip_preserves_data_context() -> None:
    stock = StockIdentity(code="600519", name="贵州茅台")
    context = DataContext(stock=stock, quote={"price": 1688.0}, diagnostics=[{"kind": "quote", "ok": True}])
    report = AnalysisReport(
        task_id="task-1",
        stock=stock,
        status=AnalysisStatus.REPORT_READY,
        action=DecisionAction.WATCH,
        confidence=ConfidenceLevel.MEDIUM,
        summary="summary",
        reasons=["reason"],
        risks=[RiskFinding(level="low", message="risk")],
        agent_views=[AgentView(agent="agent", conclusion="view")],
        data_context=context,
    )

    payload = report.to_dict()
    restored = AnalysisReport.from_dict(payload)

    assert payload["data_context"]["quote"]["price"] == 1688.0
    assert restored == report
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_analysis_contracts.py -v`

预期：FAIL，报错包含 `AttributeError: 'DataContext' object has no attribute 'to_dict'` 或 `AnalysisReport` 没有 `from_dict`。

- [ ] **步骤 3：实现 round-trip 契约**

在 `contracts.py` 中为 `DataContext` 增加：

```python
    def to_dict(self) -> dict[str, Any]:
        return {
            "stock": self.stock.to_dict(),
            "quote": dict(self.quote),
            "technicals": dict(self.technicals),
            "fundamentals": dict(self.fundamentals),
            "news": list(self.news),
            "gaps": list(self.gaps),
            "diagnostics": list(self.diagnostics),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DataContext":
        stock_payload = payload.get("stock", {})
        stock = StockIdentity(
            code=str(stock_payload.get("code", "")),
            name=str(stock_payload.get("name", "")),
            market=str(stock_payload.get("market", "cn")),
        )
        return cls(
            stock=stock,
            quote=dict(payload.get("quote", {})),
            technicals=dict(payload.get("technicals", {})),
            fundamentals=dict(payload.get("fundamentals", {})),
            news=list(payload.get("news", [])),
            gaps=list(payload.get("gaps", [])),
            diagnostics=list(payload.get("diagnostics", [])),
        )
```

修改 `AnalysisReport.to_dict()` 增加：

```python
"data_context": self.data_context.to_dict(),
```

为 `AnalysisReport` 增加：

```python
    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AnalysisReport":
        stock_payload = payload.get("stock", {})
        stock = StockIdentity(
            code=str(stock_payload.get("code", "")),
            name=str(stock_payload.get("name", "")),
            market=str(stock_payload.get("market", "cn")),
        )
        context_payload = payload.get("data_context") or {
            "stock": stock.to_dict(),
            "gaps": list(payload.get("data_gaps", [])),
            "diagnostics": list(payload.get("data_diagnostics", [])),
        }
        return cls(
            task_id=str(payload["task_id"]),
            stock=stock,
            status=AnalysisStatus(str(payload["status"])),
            action=DecisionAction(str(payload["action"])),
            confidence=ConfidenceLevel(str(payload["confidence"])),
            summary=str(payload.get("summary", "")),
            reasons=list(payload.get("reasons", [])),
            risks=[RiskFinding(level=str(item.get("level", "")), message=str(item.get("message", ""))) for item in payload.get("risks", [])],
            agent_views=[AgentView(agent=str(item.get("agent", "")), conclusion=str(item.get("conclusion", ""))) for item in payload.get("agent_views", [])],
            data_context=DataContext.from_dict(context_payload),
        )
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_analysis_contracts.py -v`

预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/domains/analysis/contracts.py services/api/tests/test_analysis_contracts.py
git commit -m "feat: serialize analysis reports" -m "Outline:
- Add DataContext round-trip serialization.
- Add AnalysisReport restoration from serialized payloads.
- Preserve legacy data_gaps and data_diagnostics while exposing full data_context."
```

---

### 任务 2：Report repository 契约与内存实现

**文件：**

- 创建：`services/api/money_api/domains/analysis/report_repository.py`
- 创建：`services/api/tests/test_report_repository.py`

- [ ] **步骤 1：编写失败的测试**

```python
from money_api.domains.analysis.contracts import AnalysisReport, AnalysisStatus, ConfidenceLevel, DataContext, DecisionAction, StockIdentity
from money_api.domains.analysis.report_repository import AnalysisReportRecord, InMemoryAnalysisReportRepository


def build_report(task_id: str, summary: str = "summary") -> AnalysisReport:
    stock = StockIdentity(code="600519", name="贵州茅台")
    return AnalysisReport(
        task_id=task_id,
        stock=stock,
        status=AnalysisStatus.REPORT_READY,
        action=DecisionAction.WATCH,
        confidence=ConfidenceLevel.MEDIUM,
        summary=summary,
        reasons=[],
        risks=[],
        agent_views=[],
        data_context=DataContext(stock=stock),
    )


def test_in_memory_repository_saves_and_gets_report() -> None:
    repository = InMemoryAnalysisReportRepository()
    report = build_report("task-1")

    record = repository.save(report)

    assert isinstance(record, AnalysisReportRecord)
    assert record.task_id == "task-1"
    assert repository.get("task-1") == report


def test_in_memory_repository_lists_recent_reports() -> None:
    repository = InMemoryAnalysisReportRepository()
    repository.save(build_report("task-1", "first"))
    repository.save(build_report("task-2", "second"))

    records = repository.list_recent(limit=1)

    assert [record.task_id for record in records] == ["task-2"]
    assert records[0].summary == "second"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_report_repository.py -v`

预期：FAIL，模块不存在。

- [ ] **步骤 3：实现 repository 契约与内存实现**

创建 `report_repository.py`，实现：

```python
"""Report repository contracts and implementations."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from money_api.domains.analysis.contracts import AnalysisReport


@dataclass(frozen=True)
class AnalysisReportRecord:
    task_id: str
    created_at: str
    stock: dict[str, str]
    status: str
    summary: str
    report: dict[str, object]

    @classmethod
    def from_report(cls, report: AnalysisReport, created_at: str | None = None) -> "AnalysisReportRecord":
        timestamp = created_at or datetime.now(timezone.utc).isoformat()
        payload = report.to_dict()
        return cls(
            task_id=report.task_id,
            created_at=timestamp,
            stock=report.stock.to_dict(),
            status=report.status.value,
            summary=report.summary,
            report=payload,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "created_at": self.created_at,
            "stock": dict(self.stock),
            "status": self.status,
            "summary": self.summary,
            "report": dict(self.report),
        }


class AnalysisReportRepository(Protocol):
    def save(self, report: AnalysisReport) -> AnalysisReportRecord: ...
    def get(self, task_id: str) -> AnalysisReport | None: ...
    def list_recent(self, limit: int = 20) -> list[AnalysisReportRecord]: ...


class InMemoryAnalysisReportRepository:
    def __init__(self):
        self._records: dict[str, AnalysisReportRecord] = {}

    def save(self, report: AnalysisReport) -> AnalysisReportRecord:
        record = AnalysisReportRecord.from_report(report)
        self._records[report.task_id] = record
        return record

    def get(self, task_id: str) -> AnalysisReport | None:
        record = self._records.get(task_id)
        return AnalysisReport.from_dict(record.report) if record is not None else None

    def list_recent(self, limit: int = 20) -> list[AnalysisReportRecord]:
        records = sorted(self._records.values(), key=lambda record: record.created_at, reverse=True)
        return records[:limit]
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_report_repository.py -v`

预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/domains/analysis/report_repository.py services/api/tests/test_report_repository.py
git commit -m "feat: add analysis report repository" -m "Outline:
- Define analysis report history records and repository protocol.
- Add in-memory repository for deterministic tests.
- Cover save, get, and recent-list behavior."
```

---

### 任务 3：JSON 文件 repository

**文件：**

- 修改：`services/api/money_api/domains/analysis/report_repository.py`
- 修改：`services/api/tests/test_report_repository.py`

- [ ] **步骤 1：编写失败的测试**

在 `test_report_repository.py` 追加：

```python
from money_api.domains.analysis.report_repository import JsonFileAnalysisReportRepository


def test_json_repository_saves_and_loads_report(tmp_path) -> None:
    repository = JsonFileAnalysisReportRepository(tmp_path)
    report = build_report("task-1")

    repository.save(report)

    assert repository.get("task-1") == report
    assert (tmp_path / "task-1.json").exists()


def test_json_repository_lists_recent_reports(tmp_path) -> None:
    repository = JsonFileAnalysisReportRepository(tmp_path)
    repository.save(build_report("task-1", "first"))
    repository.save(build_report("task-2", "second"))

    records = repository.list_recent(limit=2)

    assert {record.task_id for record in records} == {"task-1", "task-2"}
    assert records[0].created_at >= records[1].created_at


def test_json_repository_skips_corrupt_files(tmp_path) -> None:
    repository = JsonFileAnalysisReportRepository(tmp_path)
    repository.save(build_report("task-1"))
    (tmp_path / "broken.json").write_text("not json", encoding="utf-8")

    records = repository.list_recent(limit=20)

    assert [record.task_id for record in records] == ["task-1"]


def test_json_repository_rejects_unsafe_task_id(tmp_path) -> None:
    repository = JsonFileAnalysisReportRepository(tmp_path)
    report = build_report("../escape")

    try:
        repository.save(report)
    except ValueError as exc:
        assert "unsafe task_id" in str(exc)
    else:
        raise AssertionError("expected unsafe task_id to be rejected")
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_report_repository.py -v`

预期：FAIL，`JsonFileAnalysisReportRepository` 尚不存在。

- [ ] **步骤 3：实现 JSON repository**

在 `report_repository.py` 追加：

```python
import json
from pathlib import Path


def _safe_report_filename(task_id: str) -> str:
    if not task_id or "/" in task_id or "\\" in task_id or task_id in {".", ".."} or ".." in task_id:
        raise ValueError(f"unsafe task_id: {task_id}")
    return f"{task_id}.json"


class JsonFileAnalysisReportRepository:
    def __init__(self, reports_dir: str | Path):
        self.reports_dir = Path(reports_dir)

    def save(self, report: AnalysisReport) -> AnalysisReportRecord:
        record = AnalysisReportRecord.from_report(report)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        path = self.reports_dir / _safe_report_filename(report.task_id)
        path.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return record

    def get(self, task_id: str) -> AnalysisReport | None:
        try:
            path = self.reports_dir / _safe_report_filename(task_id)
        except ValueError:
            return None
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return AnalysisReport.from_dict(payload["report"])

    def list_recent(self, limit: int = 20) -> list[AnalysisReportRecord]:
        if not self.reports_dir.exists():
            return []
        records = []
        for path in self.reports_dir.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                records.append(
                    AnalysisReportRecord(
                        task_id=str(payload["task_id"]),
                        created_at=str(payload["created_at"]),
                        stock=dict(payload.get("stock", {})),
                        status=str(payload.get("status", "")),
                        summary=str(payload.get("summary", "")),
                        report=dict(payload.get("report", {})),
                    )
                )
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                continue
        records.sort(key=lambda record: record.created_at, reverse=True)
        return records[:limit]
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_report_repository.py -v`

预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/domains/analysis/report_repository.py services/api/tests/test_report_repository.py
git commit -m "feat: persist analysis reports as JSON" -m "Outline:
- Add JSON file repository for analysis report history.
- Protect report file paths against unsafe task IDs.
- Cover save, get, recent-list, and corrupt-file behavior."
```

---

### 任务 4：AnalysisService repository 集成

**文件：**

- 修改：`services/api/money_api/domains/analysis/service.py`
- 修改：`services/api/tests/test_analysis_service.py`

- [ ] **步骤 1：编写失败的测试**

在 `test_analysis_service.py` 中更新 `build_service()`，让它返回 service 和 repository，或新增测试：

```python
from money_api.domains.analysis.report_repository import InMemoryAnalysisReportRepository


def test_create_single_stock_analysis_saves_report_to_repository() -> None:
    repository = InMemoryAnalysisReportRepository()
    service = build_service(repository=repository)

    report = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议")

    assert repository.get(report.task_id) == report
    assert service.get_report(report.task_id) == report


def test_list_reports_returns_repository_records() -> None:
    repository = InMemoryAnalysisReportRepository()
    service = build_service(repository=repository)
    report = service.create_single_stock_analysis("贵州茅台", "请全面分析并给出投资建议")

    records = service.list_reports(limit=10)

    assert records[0].task_id == report.task_id
```

将 helper 改为：

```python
def build_service(repository=None) -> AnalysisService:
    return AnalysisService(..., report_repository=repository)
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_analysis_service.py -v`

预期：FAIL，`AnalysisService.__init__()` 不接受 `report_repository` 或没有 `list_reports`。

- [ ] **步骤 3：实现 service 集成**

修改 `service.py`：

```python
from money_api.domains.analysis.report_repository import AnalysisReportRecord, AnalysisReportRepository, InMemoryAnalysisReportRepository
```

构造函数增加：

```python
        report_repository: AnalysisReportRepository | None = None,
```

替换 `_reports`：

```python
        self.report_repository = report_repository or InMemoryAnalysisReportRepository()
```

创建报告后：

```python
        self.report_repository.save(report)
```

修改读取：

```python
    def get_report(self, task_id: str) -> AnalysisReport | None:
        return self.report_repository.get(task_id)

    def list_reports(self, limit: int = 20) -> list[AnalysisReportRecord]:
        return self.report_repository.list_recent(limit=limit)
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_analysis_service.py services/api/tests/test_report_repository.py -v`

预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/domains/analysis/service.py services/api/tests/test_analysis_service.py
git commit -m "feat: save reports through repository" -m "Outline:
- Make AnalysisService depend on an analysis report repository.
- Save created reports and read reports through the repository boundary.
- Add recent report listing at the service layer."
```

---

### 任务 5：API history 查询函数与默认 JSON repository

**文件：**

- 修改：`services/api/money_api/api/v1/router.py`
- 修改：`services/api/money_api/main.py`
- 修改：`services/api/money_api/core/config.py`
- 修改：`.env.example`
- 修改：`services/api/tests/test_analysis_api.py`

- [ ] **步骤 1：编写失败的测试**

在 `test_analysis_api.py` 修改 import：

```python
from money_api.main import analyze_stock, get_analysis_report, health, list_analysis_reports
```

追加测试：

```python
def test_list_analysis_reports_returns_recent_records() -> None:
    payload = analyze_stock("贵州茅台", "请全面分析并给出投资建议")

    records = list_analysis_reports(limit=5)

    assert records
    assert records[0]["task_id"] == payload["task_id"]
    assert records[0]["stock"]["code"] == "600519"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_analysis_api.py::test_list_analysis_reports_returns_recent_records -v`

预期：FAIL，`list_analysis_reports` 尚未导出。

- [ ] **步骤 3：实现 API 查询与配置**

在 `core/config.py` 的 `Settings` 增加：

```python
analysis_reports_dir: str = os.getenv("MONEY_REPORTS_DIR", "data/cache/reports")
```

在 `.env.example` 增加：

```dotenv
MONEY_REPORTS_DIR=data/cache/reports
```

在 `router.py` 增加 imports：

```python
from money_api.core.config import settings
from money_api.domains.analysis.report_repository import AnalysisReportRepository, JsonFileAnalysisReportRepository
```

给 `build_default_analysis_service()` 增加参数：

```python
def build_default_analysis_service(report_repository: AnalysisReportRepository | None = None) -> AnalysisService:
```

传入：

```python
report_repository=report_repository or JsonFileAnalysisReportRepository(settings.analysis_reports_dir),
```

给其他 service 工厂也接受可选 `report_repository` 并传给 `AnalysisService`。

新增：

```python
def list_analysis_reports(limit: int = 20) -> list[dict[str, object]]:
    return [record.to_dict() for record in _analysis_service.list_reports(limit=limit)]
```

在 `main.py` 增加：

```python
def list_analysis_reports(limit: int = 20) -> list[dict[str, object]]:
    from money_api.api.v1.router import list_analysis_reports as list_analysis_reports_v1

    return list_analysis_reports_v1(limit=limit)
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_analysis_api.py services/api/tests/test_analysis_service.py -v`

预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/api/v1/router.py services/api/money_api/main.py services/api/money_api/core/config.py .env.example services/api/tests/test_analysis_api.py
git commit -m "feat: expose analysis report history" -m "Outline:
- Add API-level report history listing.
- Use JSON report repository in the default analysis service.
- Add reports directory configuration and API coverage."
```

---

### 任务 6：文档与最终验证

**文件：**

- 修改：`README.md`
- 修改：`docs/stages.md`

- [ ] **步骤 1：更新 README 当前实现切片**

将当前实现切片的阶段描述更新为：

```markdown
当前阶段已经完成真实 A 股数据层、TradingAgents 深度引擎边界，并新增报告历史能力：分析结果会通过 repository 保存，支持按 `task_id` 读取和列出最近报告。
```

- [ ] **步骤 2：更新 stages 状态**

在 `docs/stages.md` 中：

- 将阶段 4 状态改为 `已完成`。
- 当前阶段结论改为阶段 4 完成内容。
- 记录默认离线测试结果。
- 下一阶段建议改为阶段 5“Web 工作台”。

- [ ] **步骤 3：运行最终验证**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -v`

预期：PASS。

运行：`git diff --check README.md docs/stages.md docs/superpowers/plans/2026-07-01-stage-4-report-history.md docs/superpowers/specs/2026-07-01-stage-4-report-history-design.md`

预期：退出码 0，无输出。

- [ ] **步骤 4：Commit**

```bash
git add README.md docs/stages.md
git commit -m "docs: document stage 4 report history" -m "Outline:
- Update README with report history capability.
- Mark stage 4 complete in the living roadmap.
- Record validation and the next Web workbench stage direction."
```

---

## 计划自检结果

### 规格覆盖度

- Report/DataContext round-trip：任务 1 覆盖。
- Repository 协议与内存实现：任务 2 覆盖。
- JSON 文件持久化：任务 3 覆盖。
- Service 保存、读取、列表：任务 4 覆盖。
- API history 查询与默认 JSON repository：任务 5 覆盖。
- README 与阶段活文档：任务 6 覆盖。
- Web、桌面、SQLite、全文搜索、追问：明确不属于本计划。

### 红旗词扫描

计划正文不使用未完成红旗表达；每个实现步骤都包含目标文件、示例测试、实现方向、命令和提交大纲。

### 类型一致性

- `DataContext.to_dict/from_dict` 和 `AnalysisReport.from_dict` 在任务 1 定义，任务 2-5 复用。
- `AnalysisReportRecord`、`AnalysisReportRepository`、`InMemoryAnalysisReportRepository` 在任务 2 定义。
- `JsonFileAnalysisReportRepository` 在任务 3 定义，任务 5 作为默认 API repository 使用。
- `AnalysisService.list_reports()` 在任务 4 定义，任务 5 API 层复用。
