# 阶段 5：Web 工作台设计规格

日期：2026-07-01
状态：已按用户批准进入设计与计划
阶段：Brainstorming 设计规格，不包含实现代码

## 1. 背景

阶段 1 到阶段 4 已经完成单股分析后端契约、真实 A 股 quote 数据层、TradingAgents 深度引擎边界和报告历史 repository。当前缺口是用户还不能通过 Web 入口发起分析、查看最近报告或阅读结构化报告详情。

`apps/web/` 目前是预留目录，没有前端框架、package.json 或构建脚本。阶段 5 的目标是先建立一个可打开、可验证、契约清晰的 Web 工作台第一版，为后续接 HTTP API、桌面壳和更复杂的报告体验打基础。

## 2. 设计选项

### 方案 A：立即引入 React/Vite

优点是工程化能力强，后续扩展状态管理、路由和组件测试更自然。缺点是会立刻引入 Node 依赖、构建脚本和 CI 成本，而当前仓库的 Web 目录尚未确定框架。

### 方案 B：静态 HTML/CSS/JS 工作台壳

使用 `apps/web/index.html`、`src/styles.css`、`src/app.js` 和 `src/mockData.js` 构建一个真正可交互的单页工作台。第一版使用本地 mock service 模拟分析、历史和详情，UI 文案与后端字段契约对齐。优点是零依赖、可直接打开、可用 Python 测试检查结构和契约。该方案推荐。

### 方案 C：先补 FastAPI HTTP 层再做 Web

优点是 Web 可以直接调用真实后端。缺点是阶段 5 会同时承担 HTTP 服务、前端页面和联调，范围过大。该方案建议作为阶段 5 后续切片或阶段 5.2。

## 3. 推荐方向

采用方案 B：静态 Web 工作台壳。

第一版不追求完整生产前端框架，而是把用户工作流和报告阅读结构做实：左侧发起分析与最近报告，中间报告详情，右侧数据诊断与风险摘要。页面默认展示真实结构字段的 mock 报告，点击“开始分析”会生成一条新的本地报告并进入详情。后续接 HTTP API 时，只需替换 `src/app.js` 中的 service 层。

## 4. 目标

阶段 5 完成后，Money_Never_sleep 应具备：

1. `apps/web/index.html` 作为 Web 工作台入口。
2. `apps/web/src/styles.css` 提供面向投研工作台的紧凑、可扫描视觉样式。
3. `apps/web/src/mockData.js` 提供与 `AnalysisReport.to_dict()` 对齐的 mock 数据。
4. `apps/web/src/app.js` 提供本地分析、历史列表、报告详情切换和字段渲染。
5. `apps/web/README.md` 记录打开方式、当前离线 mock 边界和后续 HTTP API 接入方向。
6. Python 测试覆盖 Web 入口文件、关键 UI 区域、mock 报告字段和 JS service 边界。
7. README 和 `docs/stages.md` 记录阶段 5 状态、验证结果和下一步建议。

## 5. 非目标

阶段 5 第一版不做：

- 不引入 React/Vite/Next 等前端框架。
- 不接真实 HTTP API。
- 不做登录、权限、用户体系。
- 不做复杂图表、K 线、实时行情轮询。
- 不做桌面端打包。
- 不做移动端专项适配，但页面必须在窄屏下可用。

## 6. 页面结构

第一屏就是工作台，不做营销 landing。

建议布局：

```text
Header: Money_Never_sleep / 状态 / 当前模式
Main:
  Left panel: 单股分析表单 + 最近报告列表
  Center panel: 当前报告详情
  Right panel: 数据诊断 + 风险和后续动作
```

关键区块：

- 分析表单：股票输入、问题输入、深度分析开关或固定深度分析按钮。
- 最近报告：显示股票、状态、时间、摘要。
- 报告详情：action、confidence、summary、reasons、agent views。
- 诊断区：data gaps、data diagnostics、数据上下文快照。
- 空状态：无报告时显示可操作的初始提示，但不占用整页做介绍。

## 7. 数据契约

前端 mock 报告应使用后端现有字段：

- `task_id`
- `stock`
- `status`
- `action`
- `confidence`
- `summary`
- `reasons`
- `risks`
- `agent_views`
- `data_gaps`
- `data_diagnostics`
- `data_context`

本地生成报告时，应保持同样结构，方便后续替换为 API 调用。

## 8. 交互行为

1. 页面加载时展示 mock 最近报告列表，并默认选中第一条报告。
2. 用户输入股票和问题后点击开始分析。
3. 本地 service 生成一条新报告，插入最近报告列表顶部。
4. 报告详情切换到新报告。
5. 点击历史报告可切换详情。
6. 风险、诊断和 agent views 为空时显示简洁空状态。

## 9. 测试策略

默认测试仍使用 Python/pytest：

- 检查 `apps/web/index.html` 存在并引用 CSS/JS。
- 检查页面包含分析表单、报告列表、详情、诊断区。
- 检查 `mockData.js` 暴露与后端字段对齐的数据。
- 检查 `app.js` 包含 service 边界函数和渲染入口。
- 运行 `python -m pytest services/api/tests -q`，确保后端无回归。
- 运行 `python -m py_compile` 不适用于 JS；用 `node --check apps/web/src/app.js` 和 `node --check apps/web/src/mockData.js` 做语法验证。如果本机没有 node，则记录未验证项。

## 10. 验收标准

阶段 5 实现完成后验收标准为：

1. `apps/web/index.html` 可直接用浏览器打开并看到工作台。
2. 用户可以在页面中本地发起一次 mock 分析并看到新报告。
3. 用户可以切换最近报告并查看结构化详情。
4. Web mock 数据字段与后端 `AnalysisReport.to_dict()` 兼容。
5. `services/api/tests` 默认离线测试通过。
6. Web 文件语法和结构检查通过。
7. README 和 `docs/stages.md` 更新阶段 5 状态、验证结果和下一阶段建议。

## 11. 下一步

使用 writing-plans 创建阶段 5 实现计划。实现计划应拆成小任务：

1. Web 工作台静态文件和结构测试。
2. Mock 数据契约。
3. 前端交互和渲染逻辑。
4. Web README 与验证脚本或测试。
5. 阶段文档与最终验证。
