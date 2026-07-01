# 阶段路线图

状态：活文档
最近更新：2026-07-01

本文档用于记录 Money_Never_sleep 每个阶段要完成什么、验收标准、当前状态和后续想法。后续有新的判断、优先级变化或产品想法时，优先更新本文档，再进入实现计划。

## 更新规则

- 每完成一个阶段，更新对应阶段的状态、交付物、验证结果和下一步建议。
- 当新增想法影响阶段范围、顺序或验收标准时，先更新本文档，再拆分实现计划。
- 当阶段改变项目定位、用户可见能力、安装/使用命令、API 入口、Web/Desktop 工作流、打包方式或重大架构方向时，同步更新 `README.md`。
- README 默认使用中文；需要英文时提供英文 section 或英文文档链接。
- 可以主动调用任何对当前目标有帮助的 skills，例如在进入阶段 2“真实 A 股数据层”前，先使用 brainstorming 完成设计规格，再使用 writing-plans 形成实现计划；仍需遵守各 skill 的用户批准关卡和仓库安全规则。
- `docs/information-map.md` 是后续 agent 的信息地图；它必须说明去哪里找什么，以及完成工作后去哪里留下什么信息。
- 所有第一版暂时没做、需要改进、后续必须回来补齐的事项，统一记录到 `docs/improvement-backlog.md`，不要只留在对话或 commit message 中。
- 每完成阶段、改变架构方向或留下重要限制时，同步更新 `docs/agent-handoff.md`，让后续 agent 能理解之前做了什么、为什么做、收益是什么、还没做什么、下一步建议怎么做。

## 状态说明

- `已完成`：代码、文档、验证和提交已完成。
- `进行中`：正在实现或正在审查。
- `待计划`：方向明确，但尚未形成实现计划。
- `待决策`：需要先做技术或产品取舍。

## 阶段总览

| 阶段 | 状态 | 目标 | 主要交付物 | 验收标准 |
| --- | --- | --- | --- | --- |
| 0. 项目边界与设计 | 已完成 | 明确 Money_Never_sleep 不直接 fork 参考项目，而是自建平台骨架 | 设计规格、实现计划、README 初始说明 | 设计文档和实现计划已提交 |
| 1. 单股分析后端契约 | 已完成 | 建立可测试的单股深度分析 dry-run 后端闭环 | 领域契约、股票解析、数据上下文、Agent 适配器、分析服务、Python API | `services/api/tests` 全部通过 |
| 2. 真实 A 股数据层 | 已完成 | 用真实 provider 替换当前离线 fixture，并保留 fallback 和数据缺口语义 | ProviderResult 契约、DataContext diagnostics、腾讯 quote parser/provider、可选 network smoke | 离线测试通过，至少一个真实样例可手动验证 |
| 3. TradingAgents 深度引擎接入 | 已完成 | 将 TradingAgents-astock 作为 DeepResearchEngine 的真实实现接入 | TradingAgents adapter、runner 协议、真实 runner 壳、配置入口、可选 smoke | mock 与真实引擎可切换，opt-in 真实 smoke 已验证可运行 |
| 4. 报告、历史与复盘 | 已完成 | 保存报告和分析上下文，支持历史查询、复盘和追问 | 报告 round-trip 契约、repository、JSON 持久化、历史查询 API | 报告可重复读取，关键证据和 data gaps 可追溯 |
| 5. Web 工作台 | 已完成 | 提供用户可操作的单股分析入口和报告阅读体验 | 静态 Web 工作台、离线 mock 分析、最近报告、报告详情、数据诊断 | 用户可从 Web 发起 mock 分析并查看结构化报告 |
| 5.5 HTTP API 层 | 已完成 | 为 Web 和桌面提供真实 JSON HTTP 边界 | HTTP dispatcher、标准库 server、Web API mode | 客户端可通过 HTTP 发起分析、读取报告和最近报告 |
| 5.6 HTTP 任务队列与状态轮询 | 已完成 | 让 Web/桌面在真实 API 模式下可异步发起分析并轮询状态 | in-memory task queue、`POST /tasks/analysis`、`GET /tasks/{id}`、Web 轮询 | 真实 API 模式下分析请求不再依赖长同步阻塞 |
| 5.7 任务持久化与恢复 | 已完成 | 让任务在服务重启后仍可查询，并标记中断任务 | JSON task repository、`GET /tasks`、恢复中断任务为 failed | 重启后仍可查看近期任务，并知道哪些任务被中断 |
| 5.8 任务取消与重试 | 已完成 | 让任务具备最小控制面，而不必等待服务端完全重构 | `POST /tasks/{id}/cancel`、`POST /tasks/{id}/retry`、cancelled 状态 | 服务端可取消非终态任务，并基于失败/取消任务重试 |
| 5.9 任务超时回收 | 已完成 | 让长时间卡住的任务能自动收敛，而不是无限轮询 | `timeout_s`、`started_at`、读取路径上的超时标记 | 超时任务会自动转为 failed，并写明超时原因 |
| 5.10 任务 watchdog 与自动重试 | 已完成 | 让超时回收不依赖读取路径，并让可重试失败任务自动再试一次 | watchdog 扫描、`max_retries`、`retry_count` | 长任务可被后台回收，失败任务可按策略自动重试 |
| 5.11 Web 任务控制 UI | 已完成 | 让用户在页面上直接取消或重试任务 | 取消/重试按钮、当前任务状态跟踪、失败任务重试入口 | 真实 API 模式下用户可直接控制当前任务 |
| 5.12 Web 任务历史视图 | 已完成 | 让用户看到近期任务，而不只看当前任务 | 最近任务列表、`GET /tasks?limit=`、操作后刷新 | 真实 API 模式下用户可查看近期任务状态和失败原因 |
| 6. 桌面端与本地体验 | 已完成 | 决定 Electron、Tauri 或 Wails，并提供本地应用体验 | Electron 桌面壳、macOS 构建入口、Web 工作台资源打包 | macOS `.app` 可构建并能承载 Web 工作台 |
| 6.1 桌面托管本地 API | 已完成 | 让桌面端默认尝试拉起本地 API，并使用更接近可用产品的 runtime service | runtime service factory、Electron 托管 server、打包 API 源码资源 | 桌面无需手动设置 API URL 也可尝试进入真实 HTTP 模式 |
| 6.2 桌面启动诊断 | 已完成 | 让用户看到桌面当前运行模式和回退原因 | startup 上下文注入、mode pill、诊断面板启动区块 | 桌面能显示托管 API / 外部 API / 离线模式和最近错误 |
| 7. 风控、回测与组合 | 已完成 | 从单股建议扩展到纪律、验证和组合层面 | 风控纪律契约、默认风控策略、报告风险控制计划 | 建议输出带仓位、止损、止盈和免责声明 |
| 7.1 回测接口 | 已完成 | 用历史价格序列复盘报告和风控纪律 | 回测契约、确定性回测引擎、Python/HTTP API | 报告可输出收益、回撤、退出原因和持有天数 |
| 7.2 真实 K 线回测数据源 | 已完成 | 用真实日线价格序列驱动回测接口 | Sina K 线 provider、provider 回测 API、opt-in 真实网络 smoke | 回测可由行情 provider 自动获取价格序列 |
| 7.3 组合风险预算 | 已完成 | 将多份单股报告合成为组合层仓位预算 | 组合预算契约、预算器、Python/HTTP API | 输出总仓位、现金保留、单票预算和组合规则 |
| 7.4 回测成本与滑点 | 已完成 | 让回测收益表达交易摩擦和复权语义 | BacktestOptions、净收益/裸收益/成本影响、Python/HTTP API | 默认行为兼容，传参时输出成本调整后的净收益 |

## 当前阶段结论

阶段 5.12 已完成。当前系统已具备前后端贯通的异步 HTTP 任务控制与任务可见性闭环：

1. `POST /tasks/analysis` 可创建分析任务，`GET /tasks/{id}` 和 `GET /tasks?limit=` 可查询任务。
2. 任务默认持久化到 JSON 文件目录 `data/cache/tasks`，服务重启时会把上次中断的运行中任务标记为 `failed`。
3. `POST /tasks/{id}/cancel` 可取消非终态任务；`POST /tasks/{id}/retry` 可基于失败或已取消任务创建重试任务。
4. 新增 `timeout_s`、`started_at`、`retry_count` 和 `max_retries`，任务可在后台 watchdog 扫描时自动超时失败并自动重试。
5. Web 工作台现在提供 `取消任务` 和 `重试任务` 按钮，并展示最近任务历史列表。
6. 取消不是底层线程/外部引擎的强制中断；仍未实现复杂退避策略、分布式 worker、筛选分页或完整任务详情页。

离线验证命令：

```bash
PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -v
```

离线结果：`125 passed, 3 skipped`。

Sina K 线真实网络 smoke 结果：`1 passed`。

TradingAgents 真实 smoke 结果：`1 passed`。

macOS 构建结果：`apps/desktop/dist/mac-arm64/Money Never Sleep.app`。

Web 打开方式：`apps/web/index.html`。

HTTP API 模式：启动 server 后打开 `apps/web/index.html?api=http://127.0.0.1:8000`。

桌面构建命令：`cd apps/desktop && npm run build:mac`。

## 下一阶段建议

建议下一步在两个方向中二选一：补更细粒度的重试/退避策略，或继续回测与数据层的真实化增强。

## 想法池

- 把 TradingAgents-astock 接成 `DeepResearchEngine` 的真实实现。
- 借鉴 daily_stock_analysis 的数据源 fallback 和报告管理。
- 借鉴 go-stock 的行情图表、桌面体验和工具分组。
- 为每次分析保存输入数据摘要，便于后续复盘和对比。
- 后续 README 可增加英文文档链接，例如 `docs/README_EN.md`。
