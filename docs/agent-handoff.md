# Agent 交接说明

状态：活文档
最近更新：2026-07-01

本文档给后续 agent 或模型快速理解 Money_Never_sleep 已做什么、为什么这么做、收益是什么、哪些没做、下一步怎么接。它不是阶段计划的替代品；如果你刚接手，先读 `docs/information-map.md`，再读本文档。详细阶段状态看 `docs/stages.md`，未完成事项看 `docs/improvement-backlog.md`。

## 接手导航

后续 agent 或模型变更后，推荐先读：

1. `docs/information-map.md`：知道去哪里找什么、做完后写回哪里。
2. `README.md`：了解项目定位和当前能力。
3. `docs/stages.md`：确认当前阶段和下一阶段建议。
4. `docs/improvement-backlog.md`：确认第一版未做事项和优先级。
5. 本文档：理解阶段 0-5 已完成内容、设计取舍、收益和限制。

## 项目方向

Money_Never_sleep 选择“自建平台骨架 + 外部项目能力吸收”的路线：

- 不直接 fork `TradingAgents-astock`、`daily_stock_analysis` 或 `go-stock`。
- Money_Never_sleep 保持自己的领域模型、API 契约、数据契约和客户端边界。
- `TradingAgents-astock` 作为深度 AI 投研引擎参考和可选真实 runner。
- `daily_stock_analysis` 作为 API、报告、数据 fallback、Web/Desktop 工程参考。
- `go-stock` 作为桌面体验、行情图表、工具分组参考。

这样做的好处：长期边界更清楚，避免多个项目技术栈硬耦合；后续可以逐步接入真实引擎、数据源、Web、桌面、回测和组合能力。

## 已完成阶段摘要

### 阶段 0：项目边界与设计

做了什么：明确不直接 fork 参考项目，保留 Money_Never_sleep 自己的平台边界。

为什么这么做：三个参考项目价值不同，直接合并会让技术栈和职责耦合过重。

收益：后续每个能力都可以作为小切片进入，而不是一次性迁移大系统。

关键文档：

- `docs/superpowers/specs/2026-07-01-money-never-sleep-design.md`
- `docs/superpowers/plans/2026-07-01-single-stock-analysis-platform.md`

### 阶段 1：单股分析后端契约

做了什么：建立股票解析、数据上下文、Quick Agent、Mock DeepResearchEngine、AnalysisService 和 Python API。

为什么这么做：先固定单股分析闭环，让后续真实数据和真实引擎都能接到稳定接口上。

收益：默认离线可测，不依赖网络、LLM 或外部项目。

关键文件：

- `services/api/money_api/domains/analysis/contracts.py`
- `services/api/money_api/domains/analysis/context_builder.py`
- `services/api/money_api/domains/analysis/agent_engine.py`
- `services/api/money_api/domains/analysis/service.py`
- `services/api/money_api/api/v1/router.py`

### 阶段 2：真实 A 股数据层

做了什么：新增 `ProviderResult` / diagnostics 契约，`DataContextBuilder` 统一消费 provider result，接入腾讯 quote parser/provider，保留可选网络 smoke。

为什么这么做：真实数据源失败不能静默吞掉，必须能进入 data gaps 和 diagnostics。

收益：后续扩展 K 线、新闻、资金流时有统一结果和错误语义。

关键文件：

- `services/api/money_api/domains/market_data/provider_results.py`
- `services/api/money_api/domains/market_data/tencent_quote.py`
- `services/api/tests/test_tencent_quote_smoke.py`

未做事项：真实 K 线、新闻、资金流、龙虎榜、解禁等宽数据面，见 `docs/improvement-backlog.md`。

### 阶段 3：TradingAgents 深度引擎接入

做了什么：新增 TradingAgents request/result 契约、runner 协议、fake runner、`TradingAgentsDeepResearchEngine`、真实 `TradingAgentsGraphRunner` 壳和 opt-in smoke。

为什么这么做：业务层只依赖 Money_Never_sleep 的 `DeepResearchEngine`，不直接依赖 TradingAgents 内部图对象和配置。

收益：默认测试仍离线稳定，真实引擎可以显式启用并逐步验证。

关键文件：

- `services/api/money_api/domains/analysis/tradingagents_engine.py`
- `services/api/money_api/integrations/tradingagents_runner.py`
- `services/api/tests/test_tradingagents_smoke.py`

未做事项：真实 LLM/API key smoke、成本控制、超时、任务队列、DataContext 注入 TradingAgents 工具层。

### 阶段 4：报告、历史与复盘

做了什么：为 `DataContext` 和 `AnalysisReport` 增加 round-trip 序列化；新增 report repository 协议、内存 repository、JSON 文件 repository；`AnalysisService` 通过 repository 保存和读取报告；API 新增 `list_analysis_reports(limit=20)`。

为什么这么做：报告不能只存在内存里，Web 和后续复盘需要可重复读取、可追溯的历史记录。

收益：分析结果、data context、diagnostics、agent views 都能进入历史存储。

关键文件：

- `services/api/money_api/domains/analysis/report_repository.py`
- `services/api/money_api/domains/analysis/service.py`
- `services/api/money_api/main.py`

未做事项：SQLite、搜索、分页、删除、归档、标签、追问会话。

### 阶段 5：Web 工作台

做了什么：新增零依赖静态 Web 工作台，支持离线 mock 分析、最近报告列表、报告详情、风险、agent views、data gaps、diagnostics 和 data context 展示。

为什么这么做：先把用户工作流和报告阅读体验落地，避免一开始同时引入前端框架、HTTP API 和构建系统。

收益：用户可以直接打开 `apps/web/index.html` 体验第一版工作台；后续接 HTTP API 时替换 `src/app.js` 的本地 service 边界即可。

关键文件：

- `apps/web/index.html`
- `apps/web/src/mockData.js`
- `apps/web/src/app.js`
- `apps/web/src/styles.css`
- `services/api/tests/test_web_workbench.py`

未做事项：真实 HTTP API、前端框架、图表、浏览器截图验证、桌面打包。

## 当前验证命令

后端和 Web 结构默认验证：

```bash
PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -q
```

Web JS 语法验证：

```bash
node --check apps/web/src/app.js && node --check apps/web/src/mockData.js
```

可选腾讯网络 smoke：

```bash
MNS_RUN_NETWORK_SMOKE=1 PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tencent_quote_smoke.py -v
```

可选 TradingAgents smoke：

```bash
MNS_RUN_TRADINGAGENTS_SMOKE=1 PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tradingagents_smoke.py -v
```

## 当前已知限制

- 默认 Web 工作台仍是离线 mock，没有接真实 HTTP API。
- `apps/desktop` 仍没有 Electron/Tauri/Wails 配置，也没有 macOS 构建入口。
- 默认深度引擎仍是 mock；真实 TradingAgents 需要显式工厂和 opt-in smoke。
- 数据层真实 provider 只覆盖腾讯 quote 最小路径。
- 报告 repository 使用 JSON 文件，适合第一版，不适合复杂查询和并发写入。
- 没有任务队列，真实深度分析的长耗时执行还没有状态轮询。

## 推荐下一步

建议进入阶段 6：桌面端与本地体验。

推荐第一版路径：

1. 先做 Electron / Tauri / Wails 技术取舍。
2. 以当前静态 Web 工作台作为桌面第一屏。
3. 补 macOS 本地构建入口和验证命令。
4. 再考虑托盘、系统通知、本地配置目录和自动更新。

如果更想先补 Web 真联调，也可以先从 `docs/improvement-backlog.md` 的 `MNS-BL-001` 开始：设计 HTTP API，然后替换 `apps/web/src/app.js` 的本地 service。

## 给后续 agent 的注意事项

- 不要直接复制参考项目的大块源码。
- 不要把 secrets、模型名、绝对路径或本机端口写死进代码。
- 完成任何阶段时，必须更新 `README.md`、`docs/stages.md`、`docs/improvement-backlog.md` 和本文件中相关部分。
- 如果新增信息入口、文档职责或写回规则，必须更新 `docs/information-map.md`。
- 如果第一版推迟了某个功能，必须把原因和下一步写入 `docs/improvement-backlog.md`。
- 如果新增验证命令或构建入口，必须写到本文件和对应阶段文档。
