# 改进台账

状态：活文档
最近更新：2026-07-01

本文档集中记录所有第一版暂时未做、需要改善、需要回头补齐的事项。后续任何 agent 在做阶段计划、实现、收尾或发现范围外问题时，都应更新这里，而不是把待办散落在对话、commit message 或临时文件中。

## 使用规则

- 每个阶段完成时，补充或更新本阶段留下的未做事项。
- 如果实现中为了保持切片小而推迟了功能、验证、工程化或体验优化，必须在这里新增记录。
- 每条记录应说明：背景、为什么第一版没做、继续做的收益、推荐下一步、关联文件或阶段。
- 关闭一条记录时，保留条目并将状态改为 `已完成`，补充完成提交或验证依据。
- 不记录一次性临时截图、缓存、生成数据或已经明确不会做的想法。

## 状态说明

- `未开始`：明确需要做，但还没有设计或实现。
- `待设计`：需要先做规格或技术取舍。
- `待实现`：方向清楚，可以拆计划执行。
- `进行中`：已有分支或计划在推进。
- `已完成`：已实现、验证并合入。
- `暂缓`：当前阶段不做，需要等待更高优先级事项。

## 当前优先级

| ID | 状态 | 优先级 | 主题 | 为什么第一版没做 | 继续做的收益 | 推荐下一步 | 关联 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MNS-BL-001 | 已完成 | P0 | Web 接真实 HTTP API | 阶段 5 选择零依赖静态工作台，避免同时引入 HTTP 服务和前端联调 | 用户可从浏览器真实发起分析、读取历史报告 | 已在阶段 5.5 完成 dependency-free HTTP dispatcher、server 入口、基础 CORS/OPTIONS 和 Web `?api=` 模式；验证：`68 passed, 2 skipped` | 阶段 5.5、`apps/web/`、`services/api/money_api/api/http.py` |
| MNS-BL-002 | 进行中 | P0 | 桌面端技术选型与 macOS 构建入口 | `apps/desktop` 仍是预留目录，没有 Electron/Tauri/Wails 配置 | 满足本地桌面体验和用户偏好的每阶段 macOS 构建验证 | 阶段 6 正在实现 Electron 桌面壳和 macOS `.app` 构建入口 | 阶段 6、`apps/desktop/` |
| MNS-BL-013 | 待设计 | P1 | FastAPI/OpenAPI 升级 | 阶段 5.5 为避免新增依赖，先使用标准库 HTTP dispatcher | 获得 OpenAPI、自动文档、中间件和更成熟的服务化能力 | 在桌面壳或 Web 真联调稳定后，评估将 dispatcher 外层替换为 FastAPI | 阶段 5.5、`services/api/money_api/api/http.py` |
| MNS-BL-014 | 待设计 | P1 | 异步任务队列与状态轮询 | 阶段 5.5 只做同步 HTTP 调用，避免一次性引入队列和 worker | 长耗时 TradingAgents 分析可被 Web/桌面稳定轮询和恢复 | 设计 task repository、worker、`GET /tasks/{id}` 和超时/取消语义 | 阶段 5.5/6、`AnalysisStatus` |
| MNS-BL-003 | 待实现 | P1 | 真实 TradingAgents smoke | 阶段 3 只提供 opt-in smoke，默认测试不能依赖 LLM/API key | 验证真实多 Agent 投研链路可被 Money_Never_sleep 调起 | 准备本地密钥和可控样例，运行 `MNS_RUN_TRADINGAGENTS_SMOKE=1 ...test_tradingagents_smoke.py`，记录结果 | 阶段 3、`services/api/tests/test_tradingagents_smoke.py` |
| MNS-BL-004 | 待设计 | P1 | JSON 报告仓储升级为 SQLite 或可迁移仓储 | 阶段 4 为降低复杂度先使用 JSON 文件 | 提升查询、筛选、分页和并发写入能力 | 在 Web API 接入后评估 SQLite schema 和迁移策略 | 阶段 4、`report_repository.py` |
| MNS-BL-005 | 待设计 | P1 | 真实 K 线、技术指标和估值扩展 | 阶段 2 只接入腾讯 quote 最小真实路径 | 提高深度分析上下文质量，减少 mock/fixture 依赖 | 设计 provider bundle 的 K 线与 fundamentals 扩展，保持 diagnostics/gaps 语义 | 阶段 2、`domains/market_data/` |
| MNS-BL-006 | 待设计 | P1 | 新闻、公告、资金流、龙虎榜和解禁 provider | 阶段 2 明确不接宽数据面 | 支撑 A 股政策、游资、解禁等 TradingAgents 角色 | 优先选择 1-2 个高价值数据源，复用 provider result 契约 | 阶段 2/3、TradingAgents-astock 参考 |
| MNS-BL-007 | 待设计 | P1 | 分析任务状态与异步执行 | 目前 Python API 是同步函数，Web 第一版是本地 mock | 长耗时 TradingAgents 分析需要排队、状态轮询和错误恢复 | 先设计 task schema：queued/running/failed/report_ready，再接 Web 轮询 | 阶段 5 后续、`AnalysisStatus` |
| MNS-BL-008 | 待设计 | P2 | 报告追问与分析会话 | 阶段 4 只保存最终报告，没有 conversation/session | 支持围绕历史报告继续提问、补证据、复盘 | 在报告持久化稳定后设计 `AnalysisSession` 和追问记录 | 阶段 4/5 |
| MNS-BL-009 | 待设计 | P2 | 投资免责声明与风险提示治理 | 当前有风险字段，但没有统一产品级免责声明 | 降低误解为自动荐股的风险，统一 Web/API/报告表达 | 增加 report disclaimer 字段或 UI 固定风险说明 | README、Web、报告契约 |
| MNS-BL-010 | 待设计 | P2 | Web 图表和行情可视化 | 阶段 5 静态工作台不做 K 线或图表 | 改善报告阅读和行情理解效率 | 先接真实 API，再选择轻量图表方案 | 阶段 5 后续 |
| MNS-BL-011 | 待设计 | P2 | CI / 本地脚本统一入口 | 当前验证命令分散在阶段文档和对话中 | 降低换 agent 或换机器后的验证成本 | 增加 `scripts/test_api.sh`、后续 Web/Desktop 构建脚本 | `scripts/` |
| MNS-BL-012 | 待设计 | P2 | 英文文档入口 | README 规定中文默认、英文可选，但还没有英文文档 | 方便英文环境或国际协作理解项目 | 在核心功能稳定后增加 `docs/README_EN.md` | README 文档规则 |

## 按阶段遗留

### 阶段 1：单股分析后端契约

- mock deep engine 仍是默认引擎；真实 TradingAgents 需显式工厂启用。
- API 仍是 Python 函数边界，不是 HTTP 服务。

### 阶段 2：真实 A 股数据层

- 只实现腾讯 quote 最小真实路径。
- technicals、fundamentals、news 仍主要来自 static fixture 或空数据。
- network smoke 默认 skip，真实网络质量尚未持续验证。

### 阶段 3：TradingAgents 深度引擎接入

- 真实 TradingAgentsGraph 只提供 runner 壳和 opt-in smoke。
- 未解决 API key、模型成本、超时、任务队列和真实运行观测。
- 未将 Money_Never_sleep 的完整 `DataContext` 注入 TradingAgents 工具层。

### 阶段 4：报告、历史与复盘

- JSON 文件 repository 适合第一版，不适合复杂查询或并发写入。
- 未实现报告删除、归档、标签、收藏、搜索、分页。
- 未实现追问会话和复盘结果记录。

### 阶段 5：Web 工作台

- Web 是零依赖静态版本，使用离线 mock 数据。
- 未接 HTTP API，不能真实发起后端分析。
- 未引入前端框架、路由、状态管理、图表或自动化浏览器截图验证。

### 阶段 6：桌面端与本地体验

- 尚未开始。
- 当前没有 macOS 构建入口，也没有 Electron/Tauri/Wails 配置。

## 后续 agent 操作清单

开始新阶段或新任务前：

1. 读取 `docs/information-map.md` 确认信息入口和写回位置。
2. 读取 `docs/stages.md` 确认当前阶段状态。
3. 读取本文件确认未完成事项和优先级。
4. 读取 `docs/agent-handoff.md` 理解已完成架构、关键取舍和验证方式。
5. 如果新增或推迟任何事项，先更新本文件，再进入实现计划或在任务收尾时补齐。
