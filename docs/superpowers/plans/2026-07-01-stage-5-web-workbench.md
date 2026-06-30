# 阶段 5 Web 工作台实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 在 `apps/web` 建立可直接打开的单股分析 Web 工作台，支持本地发起 mock 分析、查看最近报告和阅读结构化报告详情。

**架构：** 使用零依赖静态 HTML/CSS/JS。`index.html` 定义工作台结构，`src/mockData.js` 提供与后端 `AnalysisReport.to_dict()` 对齐的数据，`src/app.js` 维护本地状态和渲染逻辑，Python 测试检查文件结构与契约。

**技术栈：** HTML、CSS、现代浏览器 JavaScript、pytest、可选 `node --check`。

---

## 范围切分

本计划只覆盖阶段 5 的最小 Web 工作台：

- Web 工作台静态入口。
- 单股分析表单。
- 最近报告列表。
- 报告详情、agent views、risks、diagnostics 和 data context 渲染。
- 本地 mock service 生成报告。
- Web 结构/契约测试。
- README 和阶段文档更新。

不实现：真实 HTTP API、React/Vite、登录权限、复杂图表、桌面打包、移动端专项设计。

## 文件结构

- 创建：`apps/web/index.html`
  Web 工作台入口，引用 CSS、mock data 和 app JS。
- 创建：`apps/web/src/styles.css`
  工作台布局、响应式规则和投研界面样式。
- 创建：`apps/web/src/mockData.js`
  与后端报告契约对齐的 mock 历史报告。
- 创建：`apps/web/src/app.js`
  本地状态、mock 分析、报告列表和详情渲染。
- 修改：`apps/web/README.md`
  记录打开方式、当前离线边界和后续 API 接入方向。
- 创建：`services/api/tests/test_web_workbench.py`
  用 pytest 检查 Web 文件、关键 DOM 区域、mock 字段和 JS service 边界。
- 修改：`README.md`
- 修改：`docs/stages.md`

---

### 任务 1：Web 工作台入口与结构测试

**文件：**

- 创建：`apps/web/index.html`
- 创建：`services/api/tests/test_web_workbench.py`

- [ ] **步骤 1：编写失败的测试**

创建 `services/api/tests/test_web_workbench.py`：

```python
from pathlib import Path


WEB_ROOT = Path("apps/web")


def read_web_file(relative_path: str) -> str:
    return (WEB_ROOT / relative_path).read_text(encoding="utf-8")


def test_web_workbench_entry_references_assets() -> None:
    html = read_web_file("index.html")

    assert '<link rel="stylesheet" href="src/styles.css">' in html
    assert '<script src="src/mockData.js"></script>' in html
    assert '<script src="src/app.js"></script>' in html


def test_web_workbench_has_core_regions() -> None:
    html = read_web_file("index.html")

    assert 'id="analysis-form"' in html
    assert 'id="report-list"' in html
    assert 'id="report-detail"' in html
    assert 'id="diagnostics-panel"' in html
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_web_workbench.py -v`

预期：FAIL，`apps/web/index.html` 尚不存在。

- [ ] **步骤 3：创建 index.html**

创建 `apps/web/index.html`：

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Money_Never_sleep Web 工作台</title>
  <link rel="stylesheet" href="src/styles.css">
</head>
<body>
  <header class="app-header">
    <div>
      <p class="eyebrow">Money_Never_sleep</p>
      <h1>单股投研工作台</h1>
    </div>
    <div class="mode-pill">离线 Mock / API 契约预览</div>
  </header>

  <main class="workbench-shell">
    <aside class="side-panel">
      <form id="analysis-form" class="analysis-form">
        <label>
          股票
          <input id="symbol-input" name="symbol" value="贵州茅台" autocomplete="off">
        </label>
        <label>
          问题
          <textarea id="message-input" name="message" rows="4">请全面分析并给出投资建议</textarea>
        </label>
        <button type="submit">开始分析</button>
      </form>

      <section class="report-list-section">
        <div class="section-heading">
          <h2>最近报告</h2>
          <span id="report-count">0</span>
        </div>
        <div id="report-list" class="report-list"></div>
      </section>
    </aside>

    <section id="report-detail" class="report-detail" aria-live="polite"></section>

    <aside id="diagnostics-panel" class="diagnostics-panel"></aside>
  </main>

  <script src="src/mockData.js"></script>
  <script src="src/app.js"></script>
</body>
</html>
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_web_workbench.py -v`

预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add apps/web/index.html services/api/tests/test_web_workbench.py
git commit -m "feat: add web workbench shell" -m "Outline:
- Add the static Web workbench entry page.
- Define analysis form, report list, report detail, and diagnostics regions.
- Cover required asset references and core regions with pytest."
```

---

### 任务 2：Mock 报告数据契约

**文件：**

- 创建：`apps/web/src/mockData.js`
- 修改：`services/api/tests/test_web_workbench.py`

- [ ] **步骤 1：编写失败的测试**

在 `test_web_workbench.py` 追加：

```python
def test_mock_data_matches_report_contract() -> None:
    mock_data = read_web_file("src/mockData.js")

    for field in (
        "task_id",
        "stock",
        "status",
        "action",
        "confidence",
        "summary",
        "reasons",
        "risks",
        "agent_views",
        "data_gaps",
        "data_diagnostics",
        "data_context",
    ):
        assert field in mock_data

    assert "window.MNS_MOCK_REPORTS" in mock_data
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_web_workbench.py::test_mock_data_matches_report_contract -v`

预期：FAIL，`mockData.js` 尚不存在。

- [ ] **步骤 3：创建 mockData.js**

创建 `apps/web/src/mockData.js`，提供两条报告。第一条至少包含：

```javascript
window.MNS_MOCK_REPORTS = [
  {
    task_id: "analysis-demo-600519",
    stock: { code: "600519", name: "贵州茅台", market: "cn" },
    status: "report_ready",
    action: "watch",
    confidence: "medium",
    summary: "趋势仍偏稳，等待更清晰的量价确认。",
    reasons: ["价格位于主要均线附近", "估值数据已进入上下文", "当前报告来自 Web 离线演示数据"],
    risks: [{ level: "medium", message: "短期波动可能放大，需结合真实数据复核" }],
    agent_views: [
      { agent: "Market Analyst", conclusion: "价格结构保持韧性，但量能确认不足" },
      { agent: "Risk Analyst", conclusion: "建议控制仓位并等待确认信号" }
    ],
    data_gaps: ["fund_flow"],
    data_diagnostics: [
      { kind: "quote", source: "tencent", ok: true, error_type: null, error_message: null, fetched_at: null, is_stale: false }
    ],
    data_context: {
      stock: { code: "600519", name: "贵州茅台", market: "cn" },
      quote: { price: 1688, source: "tencent" },
      technicals: { ma5: 1660, ma10: 1625, ma20: 1588 },
      fundamentals: { pe_ttm: 28.5, pb: 9.1 },
      news: [{ title: "示例新闻：业绩保持稳定" }],
      gaps: ["fund_flow"],
      diagnostics: []
    }
  }
];
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_web_workbench.py -v`

预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add apps/web/src/mockData.js services/api/tests/test_web_workbench.py
git commit -m "feat: add web report mock data" -m "Outline:
- Add mock reports aligned with the backend AnalysisReport payload.
- Include diagnostics, data gaps, agent views, and data context fields.
- Cover required report contract fields in Web tests."
```

---

### 任务 3：Web 交互和渲染逻辑

**文件：**

- 创建：`apps/web/src/app.js`
- 修改：`services/api/tests/test_web_workbench.py`

- [ ] **步骤 1：编写失败的测试**

在 `test_web_workbench.py` 追加：

```python
def test_app_js_exposes_service_and_render_boundaries() -> None:
    app_js = read_web_file("src/app.js")

    assert "function createLocalAnalysis" in app_js
    assert "function renderReportList" in app_js
    assert "function renderReportDetail" in app_js
    assert "function renderDiagnostics" in app_js
    assert "analysis-form" in app_js
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_web_workbench.py::test_app_js_exposes_service_and_render_boundaries -v`

预期：FAIL，`app.js` 尚不存在。

- [ ] **步骤 3：创建 app.js**

创建 `apps/web/src/app.js`，实现：

- `state = { reports, selectedTaskId }`
- `createLocalAnalysis(symbol, message)`：复制 mock 结构生成新报告。
- `renderReportList()`：渲染最近报告按钮。
- `renderReportDetail()`：渲染 summary、reasons、agent views、risks。
- `renderDiagnostics()`：渲染 data gaps、diagnostics、quote/context。
- 表单 submit：插入新报告并刷新 UI。

使用 DOM API，不依赖框架。所有用户输入进入 DOM 时使用 `textContent` 或本地 `escapeHtml()`，不要拼接未转义 HTML。

- [ ] **步骤 4：运行 JS 语法检查**

运行：`node --check apps/web/src/app.js`

预期：PASS。如果本机没有 node，记录未验证项，并继续用 pytest 验证结构。

- [ ] **步骤 5：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_web_workbench.py -v`

预期：PASS。

- [ ] **步骤 6：Commit**

```bash
git add apps/web/src/app.js services/api/tests/test_web_workbench.py
git commit -m "feat: add web workbench interactions" -m "Outline:
- Add local analysis creation and report selection behavior.
- Render report details, agent views, risks, data gaps, and diagnostics.
- Cover service and render boundaries in Web tests."
```

---

### 任务 4：工作台样式与 Web README

**文件：**

- 创建：`apps/web/src/styles.css`
- 修改：`apps/web/README.md`
- 修改：`services/api/tests/test_web_workbench.py`

- [ ] **步骤 1：编写失败的测试**

在 `test_web_workbench.py` 追加：

```python
def test_web_styles_define_workbench_layout() -> None:
    css = read_web_file("src/styles.css")

    assert ".workbench-shell" in css
    assert ".side-panel" in css
    assert ".report-detail" in css
    assert "@media" in css


def test_web_readme_documents_static_open_flow() -> None:
    readme = read_web_file("README.md")

    assert "index.html" in readme
    assert "离线 mock" in readme
    assert "HTTP API" in readme
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_web_workbench.py::test_web_styles_define_workbench_layout services/api/tests/test_web_workbench.py::test_web_readme_documents_static_open_flow -v`

预期：FAIL，CSS 尚不存在或 README 未记录新边界。

- [ ] **步骤 3：创建 CSS 与更新 README**

创建 `apps/web/src/styles.css`：

- 使用非默认系统字体栈，例如 `Avenir Next`, `PingFang SC`, `Hiragino Sans GB`, `Microsoft YaHei`, sans-serif。
- 三栏工作台布局，窄屏改为单栏。
- restrained finance palette，不用单一紫色或深蓝主题。
- 卡片圆角不超过 8px。
- 按钮、列表、状态、诊断 chips 有稳定尺寸。

更新 `apps/web/README.md`，记录：

```markdown
# Money_Never_sleep Web

当前 Web 工作台是零依赖静态版本，可直接打开 `apps/web/index.html`。

第一版使用离线 mock 数据模拟后端 `AnalysisReport` 契约，支持本地发起分析、查看最近报告和报告详情。后续接入 HTTP API 时，优先替换 `src/app.js` 中的本地 service 边界。
```

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_web_workbench.py -v`

预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add apps/web/src/styles.css apps/web/README.md services/api/tests/test_web_workbench.py
git commit -m "feat: style web workbench" -m "Outline:
- Add responsive workbench styling for the static Web app.
- Document the static open flow and offline mock boundary.
- Cover layout CSS and README guidance in Web tests."
```

---

### 任务 5：阶段文档与最终验证

**文件：**

- 修改：`README.md`
- 修改：`docs/stages.md`

- [ ] **步骤 1：更新 README 当前实现切片**

将当前实现切片描述更新为：

```markdown
当前阶段已经完成真实 A 股数据层、TradingAgents 深度引擎边界、报告历史能力，并新增 Web 工作台第一版：可直接打开静态页面进行离线 mock 分析、查看最近报告和结构化报告详情。
```

- [ ] **步骤 2：更新 stages 状态**

在 `docs/stages.md` 中：

- 将阶段 5 状态改为 `已完成`。
- 当前阶段结论改为阶段 5 完成内容。
- 记录默认离线测试结果。
- 记录 Web 打开方式：`apps/web/index.html`。
- 下一阶段建议改为阶段 6“桌面端与本地体验”。

- [ ] **步骤 3：运行最终验证**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -v`

预期：PASS。

运行：`node --check apps/web/src/app.js && node --check apps/web/src/mockData.js`

预期：PASS。如果 `node` 不存在，记录未验证项。

运行：`git diff --check README.md docs/stages.md docs/superpowers/plans/2026-07-01-stage-5-web-workbench.md docs/superpowers/specs/2026-07-01-stage-5-web-workbench-design.md apps/web/index.html apps/web/src/styles.css apps/web/src/app.js apps/web/src/mockData.js apps/web/README.md`

预期：退出码 0，无输出。

- [ ] **步骤 4：Commit**

```bash
git add README.md docs/stages.md
git commit -m "docs: document stage 5 web workbench" -m "Outline:
- Update README with the static Web workbench capability.
- Mark stage 5 complete in the living roadmap.
- Record validation and the next desktop experience direction."
```

---

## 计划自检结果

### 规格覆盖度

- Web 工作台入口：任务 1 覆盖。
- Mock 报告数据契约：任务 2 覆盖。
- 本地分析、历史列表、详情切换：任务 3 覆盖。
- 样式和 Web README：任务 4 覆盖。
- 根 README 与阶段文档：任务 5 覆盖。
- HTTP API、React/Vite、登录、图表、桌面打包：明确不属于本计划。

### 红旗词扫描

计划正文不使用未完成红旗表达；每个实现步骤都包含目标文件、示例测试、实现方向、命令和提交大纲。

### 类型一致性

- `window.MNS_MOCK_REPORTS` 在任务 2 定义，任务 3 的 `app.js` 读取同名全局。
- `createLocalAnalysis`、`renderReportList`、`renderReportDetail`、`renderDiagnostics` 在任务 3 定义，测试同名检查。
- Web 打开入口始终为 `apps/web/index.html`。
