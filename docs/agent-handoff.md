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

### 阶段 5.5：HTTP API 层

做了什么：新增 dependency-free JSON HTTP dispatcher、标准库 HTTP server 入口、基础 CORS/OPTIONS 支持，并让 Web 工作台支持 `?api=` 模式调用真实后端。

为什么这么做：Web 和桌面都需要稳定 HTTP 边界；第一版先不引入 FastAPI，减少依赖和 CI 成本。

收益：客户端可以通过 HTTP 发起分析、读取报告详情和最近报告；Web 默认仍可离线打开，并在 HTTP 请求失败时回退 mock。

关键文件：

- `services/api/money_api/api/http.py`
- `services/api/money_api/main.py`
- `services/api/tests/test_http_api.py`
- `apps/web/src/app.js`
- `apps/web/README.md`

未做事项：FastAPI/OpenAPI、完整 CORS 配置矩阵、认证、异步任务队列和长耗时轮询。

### 阶段 6：桌面端与本地体验

做了什么：选择 Electron 作为第一版桌面壳，新增 `apps/desktop` npm package、Electron main/preload、macOS `.app` 构建入口和 Web 工作台资源打包。

为什么这么做：现有 Web 工作台已经可直接加载，Electron 是当前最短路径，能最快满足 macOS 本地构建验证。

收益：仓库首次具备可构建桌面端；后续可以在同一壳里接本地 HTTP API、菜单、托盘、通知和自动更新。

关键文件：

- `apps/desktop/package.json`
- `apps/desktop/package-lock.json`
- `apps/desktop/src/main.js`
- `apps/desktop/src/preload.js`
- `services/api/tests/test_desktop_shell.py`

未做事项：签名、公证、DMG、自定义图标、自动更新、内嵌 Python API server。

### 阶段 7：风控纪律层

做了什么：新增 `RiskControlRule`、`RiskControlPlan` 和 `DefaultRiskPolicy`，让所有 `AnalysisReport` 输出结构化 `risk_controls`。

为什么这么做：分析报告不能只给 action/confidence，还需要仓位上限、止损/止盈、数据缺口降级和免责声明，方便后续复盘和纪律化执行。

收益：报告输出更克制、更可追溯，不把分析结果包装成自动交易建议。

关键文件：

- `services/api/money_api/domains/analysis/contracts.py`
- `services/api/money_api/domains/analysis/risk_policy.py`
- `services/api/money_api/domains/analysis/service.py`
- `services/api/tests/test_risk_policy.py`

未做事项：历史回测、组合风险预算、绩效归因、交易执行。

### 阶段 7.1：回测接口

做了什么：新增 `BacktestPricePoint`、`BacktestResult`、`SimpleBacktestEngine`，并通过 Python API 与 HTTP API 暴露报告回测能力。

为什么这么做：风控纪律需要能被价格序列复盘，避免报告只停留在字段层面。

收益：每份报告可以基于传入价格序列输出收益率、最大回撤、退出原因和持有天数。

关键文件：

- `services/api/money_api/domains/analysis/contracts.py`
- `services/api/money_api/domains/analysis/backtest.py`
- `services/api/money_api/domains/analysis/service.py`
- `services/api/money_api/api/http.py`
- `services/api/tests/test_backtest.py`

未做事项：真实行情数据源、交易成本、滑点、复权、组合回测。

### 阶段 7.2：真实 K 线回测数据源

做了什么：新增 Sina 日线 K 线 parser/provider，并让回测 API 支持 `source="sina"` 自动获取价格序列。

为什么这么做：阶段 7.1 只能手工传入价格序列，真实 provider 能让回测更接近用户使用场景。

收益：报告回测可以复用 market data provider 边界，后续可扩展复权、缓存和多 provider fallback。

关键文件：

- `services/api/money_api/domains/market_data/sina_kline.py`
- `services/api/tests/test_sina_kline.py`
- `services/api/money_api/domains/analysis/service.py`
- `services/api/money_api/api/http.py`

未做事项：真实网络 smoke、复权、交易成本、滑点、缓存、多 provider fallback。

## 当前验证命令

后端和 Web 结构默认验证：

```bash
PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -q
```

Web JS 语法验证：

```bash
node --check apps/web/src/app.js && node --check apps/web/src/mockData.js
```

桌面 JS 语法验证：

```bash
node --check apps/desktop/src/main.js && node --check apps/desktop/src/preload.js
```

桌面 macOS 构建：

```bash
cd apps/desktop && npm run build:mac
```

产物：`apps/desktop/dist/mac-arm64/Money Never Sleep.app`。

HTTP API 本地启动：

```bash
PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -c "from money_api.main import run_http_server; run_http_server()"
```

启动后 Web API 模式：`apps/web/index.html?api=http://127.0.0.1:8000`。

可选腾讯网络 smoke：

```bash
MNS_RUN_NETWORK_SMOKE=1 PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tencent_quote_smoke.py -v
```

Sina K 线目前只有离线 fixture 测试；真实网络 smoke 记录在 `docs/improvement-backlog.md` 的 `MNS-BL-022`。

可选 TradingAgents smoke：

```bash
MNS_RUN_TRADINGAGENTS_SMOKE=1 PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tradingagents_smoke.py -v
```

## 当前已知限制

- Web 工作台默认仍是离线 mock；真实 HTTP API 需要通过 `?api=` 显式启用。
- `apps/desktop` 已有 Electron 第一版壳和 macOS `.app` 构建入口，但尚未签名、公证、打 DMG、设置图标或内嵌 Python API server。
- 默认深度引擎仍是 mock；真实 TradingAgents 需要显式工厂和 opt-in smoke。
- 数据层真实 provider 只覆盖腾讯 quote 最小路径。
- 报告 repository 使用 JSON 文件，适合第一版，不适合复杂查询和并发写入。
- 没有任务队列，真实深度分析的长耗时执行还没有状态轮询。
- 风控纪律层已完成第一版，但尚未接回测和组合风险预算。
- 回测接口已完成第一版，但只接受传入价格序列，尚未接真实行情和交易成本模型。

## 推荐下一步

建议继续阶段 7 后续切片：回测接口或组合风险预算；如果更偏产品化，可以先做真实链路验证和桌面签名/DMG。

推荐第一版路径：

1. 设计产品级风险纪律和免责声明。
2. 建立可复盘的信号/建议记录。
3. 再考虑回测、组合、绩效归因。
4. 桌面端可并行补签名、公证、DMG、图标和自动更新。

如果更想继续服务化，可以从 `docs/improvement-backlog.md` 的 `MNS-BL-013` 或 `MNS-BL-014` 开始：升级 FastAPI/OpenAPI，或设计异步任务队列和状态轮询。

## 给后续 agent 的注意事项

- 不要直接复制参考项目的大块源码。
- 不要把 secrets、模型名、绝对路径或本机端口写死进代码。
- 完成任何阶段时，必须更新 `README.md`、`docs/stages.md`、`docs/improvement-backlog.md` 和本文件中相关部分。
- 如果新增信息入口、文档职责或写回规则，必须更新 `docs/information-map.md`。
- 如果第一版推迟了某个功能，必须把原因和下一步写入 `docs/improvement-backlog.md`。
- 如果新增验证命令或构建入口，必须写到本文件和对应阶段文档。
