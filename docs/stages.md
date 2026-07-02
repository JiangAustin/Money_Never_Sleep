# 阶段路线图

状态：活文档
最近更新：2026-07-03

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
| 5.13 任务重试退避调度 | 已完成 | 让自动重试不再立即触发，并对下一次重试时间可解释 | `next_retry_at`、指数退避调度、watchdog 到点派生重试 | 失败任务会先进入计划重试状态，到点后再派生重试任务 |
| 5.14 任务重试策略细化 | 已完成 | 让重试策略支持抖动与超时倍率，并保持默认兼容 | `retry_backoff_factor`、`retry_jitter_ratio`、`retry_timeout_multiplier` | timeout 类任务可应用更保守延迟，重试调度支持抖动 |
| 5.15 任务重试策略可观测性 | 已完成 | 让任务历史能看见重试延迟和策略命中信息 | `next_retry_delay_s`、`next_retry_policy`、Web 历史展示 | 调用方可看到本次计划重试为何延迟、延迟多久 |
| 5.16 真实个股新闻数据接入 | 已完成 | 让 runtime 分析上下文的新闻字段来自真实资讯流 | `EastmoneyNewsProvider`、runtime news 装配、provider 测试 | tencent runtime 模式下 news 来源变为 `eastmoney` |
| 5.17 runtime 默认深度引擎 auto 模式 | 已完成 | 让默认链路优先尝试真实 TradingAgents，失败时自动回退 mock | `AutoFallbackDeepResearchEngine`、runtime default `auto`、桌面默认值同步 | 默认 runtime 具备“真实优先、失败回退”的深度分析语义 |
| 5.18 runtime 市场快讯接入 | 已完成 | 让默认 news 上下文同时覆盖个股新闻与市场快讯 | `ClsMarketFlashProvider`、`CompositeNewsProvider`、runtime news 合并 | 默认 runtime 的 `news` 同时包含东方财富个股新闻和 CLS 快讯 |
| 5.19 runtime 公司公告标题流接入 | 已完成 | 让默认 news 上下文继续覆盖公司正式公告标题 | `SinaBulletinProvider`、runtime news 合并 | 默认 runtime 的 `news` 同时包含个股新闻、市场快讯和公告标题 |
| 5.20 结构化事件流与引擎可见性 | 已完成 | 把新闻/公告标题升级为首个结构化事件切片，并让报告显式展示数据来源、引擎来源和回退原因 | `MarketEvent`、事件分类器、report provenance、Web/diagnostics 展示 | 报告和 UI 能显示结构化事件、`data_sources`、`engine_source`、`engine_mode` 与 `fallback_reason` |
| 5.20 review 补强 | 已完成 | 采纳 review 中必须修改和建议修改，补兼容性、多事件抽取和长期计划规则 | 未知事件降级、单条资讯多事件、旧报告 provenance 回填、参考项目整合地图、模型使用规则 | 目标测试通过，后续计划能追踪三个参考项目和治理事项 |
| 5.21 投资计划契约 | 已完成 | 让报告输出更接近基金经理式的执行计划层 | `InvestmentPlan`、`AnalysisReport` 序列化、`AnalysisService` 自动生成、Web 详情展示 | 报告可直接显示入场条件、退出条件、复核条件和观察窗口 |
| 5.22 数据可信度评分 | 已完成 | 让报告显式给出数据可信度、扣分项和正向信号 | `DataTrustScore`、评分逻辑、报告序列化、`AnalysisService` 自动生成、Web 详情展示 | 报告可直接显示可信度分数、等级、数据源、缺口和诊断计数 |
| 5.23 引擎运行画像 | 已完成 | 让报告显式给出运行时长、执行路径、请求次数和失败信息 | `EngineTelemetry`、运行时统计、报告序列化、`AnalysisService` 自动生成、Web 详情展示 | 报告可直接显示引擎路径、成本层级、耗时和失败原因 |
| 5.24 引擎成本治理 | 已完成 | 让报告显式给出成本阈值、告警和预算命中情况 | `EngineCostGuardrail`、阈值判断、告警列表、报告序列化、Web 详情展示 | 报告可直接显示是否超预算、触发了哪些告警以及建议的治理结论 |
| 5.25 结构化事件覆盖扩展 | 已完成 | 在第一版事件切片上继续补充更高价值的回购和股权质押事件 | `MarketEventType` 扩展、事件规则扩展、Web mock 事件样例 | 报告和 UI 可展示回购、质押等更高价值的 A 股事件信号 |
| 5.26 结构化事件优先级 | 已完成 | 让事件层显式携带优先级，方便后续计划层排序和解释 | `MarketEvent.priority`、分类优先级映射、Web 事件展示 | 报告和 UI 可直接看出哪些事件属于高优先级信号 |
| 5.27 事件优先级驱动计划 | 已完成 | 让高优先级事件直接影响投资计划方向和仓位 | `AnalysisService` 事件信号汇总、计划方向推导、仓位调整 | 报告能根据正负高优先级事件把 `watch` 推向 `buy` 或 `wait` |
| 5.28 结构化事件证据范围 | 已完成 | 让事件层显式区分命中来自标题、正文还是两者 | `MarketEvent.evidence_scope`、标题/正文命中判定、Web 事件展示 | 报告和 UI 可直接看出事件证据是标题、正文还是两者都命中 |
| 5.29 结构化事件证据片段 | 已完成 | 让事件层给出实际命中的原文片段 | `MarketEvent.evidence_excerpt`、命中片段截取、Web 事件展示 | 报告和 UI 可直接看出触发事件的标题或正文片段 |
| 5.30 结构化事件正文可读性 | 已完成 | 让正文命中的事件在报告里更容易被直接读懂 | `MarketEvent.evidence_excerpt`、正文片段展示、Web 事件展示 | 报告和 UI 可直接读出正文命中的具体原文片段 |
| 5.31 结构化事件增持信号 | 已完成 | 在高价值事件流中补充股东增持这一正向信号 | `MarketEventType.SHARE_INCREASE`、事件规则扩展、Web mock 事件样例 | 报告和 UI 可展示股东增持事件，并把它纳入计划方向推导 |
| 5.32 在线工具数据层与工具驱动回退 | 已完成 | 把 runtime 从“半真实原型”升级成“在线数据优先、工具驱动兜底”的研究助手 | 腾讯 quote、Sina 技术指标、东财 F10 基本面、可选同花顺问财、tool-driven fallback | tencent runtime 模式下 quote/technicals/fundamentals/news 均可来自真实或可配置在线源，auto 失败后回退到工具驱动报告 |
| 5.33 Agent 研究工具入口 | 已完成 | 把现有在线数据层包装成可直接调用的研究工具目录 | `ResearchToolService`、`POST /research/context`、`/research/quote`、`/research/technicals`、`/research/fundamentals`、`/research/news` | 外部 agent 或上层工作流可直接按工具粒度拉取在线研究数据，而不是只能调用整份分析报告 |
| 5.34 研究工具薄切片扩展 | 已完成 | 在研究工具目录上补齐资金流、龙虎榜和解禁入口 | `POST /research/capital-flow`、`/research/longhubang`、`/research/unlocks`、对应 Python wrapper | 外部 agent 或上层工作流可以直接按资金流、龙虎榜和解禁粒度拉取在线研究数据 |
| 5.35 Web 研究工具调试面板 | 已完成 | 让 Web 工作台直接查看研究工具的原始返回值，便于验证 provider 和调试回退 | 诊断区调试面板、自动拉取 `context / quote / technicals / fundamentals / news / capital-flow / longhubang / unlocks`、可展开原始 JSON | 用户可以在 Web 里直接看见各研究工具返回内容，而不是只看整份分析报告 |
| 5.36 公告正文薄切片 | 已完成 | 让公告标题流升级为标题+正文薄切片，提升结构化事件命中质量 | `SinaBulletinProvider` 正文抓取与清洗、公告详情页解析、`news`/`events` 直接消费正文 | 用户在报告里看到的不再只是公告标题，还能看到公告正文命中的事件线索 |
| 5.37 投资计划证据范围回写 | 已完成 | 让投资计划理由和风险说明显式展示证据范围，避免计划层继续黑箱化 | `InvestmentPlan` 理由/风险说明回写、标题/正文命中解释、计划解释文本更新 | 用户可直接从计划里看出本次建议主要依赖标题、正文还是两者都命中 |
| 5.38 投资计划正负证据拆线 | 已完成 | 让投资计划的正向依据和风险依据分别展示来源，增强可执行性 | `InvestmentPlan` 正向/风险证据拆线、理由/风险说明分流 | 用户可分别看出做多依据和防守依据各自主要来自标题、正文还是两者都命中 |
| 5.39 投资计划证据展示 | 已完成 | 让 Web 报告详情页直接显示投资计划的证据来源摘要 | 投资计划区块新增“证据来源”小节、离线 mock 同步字段 | 用户可在投资计划区块里直接看到正向证据和风险证据摘要 |
| 5.40 报告列表证据摘要 | 已完成 | 让报告列表页也能直接扫到投资计划的证据方向 | 报告列表卡片新增证据摘要、离线 mock 同步字段 | 用户可在列表页直接看出当前报告偏正向还是偏风险 |
| 5.41 任务历史证据摘要 | 已完成 | 让任务历史页也能扫到同源证据摘要 | 任务历史行新增证据摘要、报告缓存回填 | 用户可在任务历史里直接看出已完成任务的证据方向 |
| 5.42 auto 回退提示 | 已完成 | 让 auto 模式在真实 TradingAgents 缺少凭据或运行失败时给出可读回退提示 | auto 回退说明、凭据提示、失败原因展开 | 用户可直接看懂为什么当前回退到了工具驱动分析 |
| 6. 桌面端与本地体验 | 已完成 | 决定 Electron、Tauri 或 Wails，并提供本地应用体验 | Electron 桌面壳、macOS 构建入口、Web 工作台资源打包 | macOS `.app` 可构建并能承载 Web 工作台 |
| 6.1 桌面托管本地 API | 已完成 | 让桌面端默认尝试拉起本地 API，并使用更接近可用产品的 runtime service | runtime service factory、Electron 托管 server、打包 API 源码资源 | 桌面无需手动设置 API URL 也可尝试进入真实 HTTP 模式 |
| 6.2 桌面启动诊断 | 已完成 | 让用户看到桌面当前运行模式和回退原因 | startup 上下文注入、mode pill、诊断面板启动区块 | 桌面能显示托管 API / 外部 API / 离线模式和最近错误 |
| 7. 风控、回测与组合 | 已完成 | 从单股建议扩展到纪律、验证和组合层面 | 风控纪律契约、默认风控策略、报告风险控制计划 | 建议输出带仓位、止损、止盈和免责声明 |
| 7.1 回测接口 | 已完成 | 用历史价格序列复盘报告和风控纪律 | 回测契约、确定性回测引擎、Python/HTTP API | 报告可输出收益、回撤、退出原因和持有天数 |
| 7.2 真实 K 线回测数据源 | 已完成 | 用真实日线价格序列驱动回测接口 | Sina K 线 provider、provider 回测 API、opt-in 真实网络 smoke | 回测可由行情 provider 自动获取价格序列 |
| 7.3 组合风险预算 | 已完成 | 将多份单股报告合成为组合层仓位预算 | 组合预算契约、预算器、Python/HTTP API | 输出总仓位、现金保留、单票预算和组合规则 |
| 7.4 回测成本与滑点 | 已完成 | 让回测收益表达交易摩擦和复权语义 | BacktestOptions、净收益/裸收益/成本影响、Python/HTTP API | 默认行为兼容，传参时输出成本调整后的净收益 |

## 当前阶段结论

阶段 5.38 已完成。当前系统已具备前后端贯通的异步 HTTP 任务控制与任务可见性闭环，并继续补齐真实输入面：

1. `POST /tasks/analysis` 可创建分析任务，`GET /tasks/{id}` 和 `GET /tasks?limit=` 可查询任务。
2. 任务默认持久化到 JSON 文件目录 `data/cache/tasks`，服务重启时会把上次中断的运行中任务标记为 `failed`。
3. `POST /tasks/{id}/cancel` 可取消非终态任务；`POST /tasks/{id}/retry` 可基于失败或已取消任务创建重试任务。
4. 新增 `timeout_s`、`started_at`、`retry_count`、`max_retries`、`next_retry_at`、`next_retry_delay_s` 和 `next_retry_policy`，任务可在后台 watchdog 扫描时自动超时失败，并保留下一次重试的决策信息。
5. `retry_backoff_factor`、`retry_jitter_ratio` 和 `retry_timeout_multiplier` 支持按错误类型（timeout）应用倍率并附加抖动。
6. runtime service 在 `MONEY_MARKET_DATA_MODE=tencent` / `online` 下，`quote` 来自腾讯，`technicals` 来自 Sina K 线，`fundamentals` 来自东财 F10 + 可选同花顺问财，`news` 来自东方财富个股新闻、CLS 市场快讯和新浪公告标题。
7. runtime service 现在会把东方财富个股新闻、CLS 市场快讯和新浪公告标题合并到同一个 `news` 上下文中，保持现有 schema 不变。
8. runtime deep engine 默认值现在是 `auto`：优先尝试真实 TradingAgents，若导入或运行失败则自动回退到工具驱动分析，并在 diagnostics 中保留失败来源。
9. runtime service 现在会把 Sina K 线、东财 F10 和可选同花顺问财接成同一个在线数据层，不再依赖静态 fixture 作为默认输入。
10. 报告现在会显式带上 `data_sources`、`engine_source`、`engine_mode` 和 `fallback_reason`，Web/diagnostics 区域也会把这些 provenance 信息直接展示出来。
11. Web 工作台现在提供 `取消任务` 和 `重试任务` 按钮，并在最近任务列表中展示下一次重试时间、策略标签和延迟秒数。
12. 结构化事件流目前已经扩展到业绩预告、减持、担保、解禁、回购和股权质押等高价值事件类型，并为事件补上了优先级；同一条资讯同时命中多类事件时会保留多条结构化事件，但还不是完整事件抽取引擎。
13. 事件优先级已经进入 `InvestmentPlan` 生成：高优先级正向事件在深度分析时可以把 `watch` 推向 `buy`，高优先级风险事件可以把计划收缩到 `wait`。
14. 结构化事件现在还能标出证据范围：标题命中、正文命中或标题与正文都命中，便于后续判断置信解释和抽取质量。
15. 结构化事件现在还能给出实际命中的原文片段，用户不需要回头翻原文就能看见触发信号的出处。
16. 结构化事件的正文命中现在更容易直接阅读，正文片段会在报告中以可读原文展示出来。
17. 结构化事件流已经补进股东增持这一正向信号，它会进入事件优先级和计划方向推导。
18. 报告历史列表兼容旧 JSON 格式：如果顶层缺少 provenance 字段，会从内层 `report` 回填。
19. 投资计划层已经有第一版 `InvestmentPlan`，但仍是基于报告和风控的规则化生成，不是从真实多 Agent 结论中学习出来的优化器。
20. 数据可信度层已经有第一版 `DataTrustScore`，但仍是基于现有 sources/gaps/diagnostics 的规则化打分，不是学习型或在线估计模型。
21. 引擎运行画像已经有第一版 `EngineTelemetry`，但仍是基于现有路径和结果的规则化治理视图，不是成本预算器或告警系统。
22. 引擎成本治理已经有第一版 `EngineCostGuardrail`，但它仍是报告级规则化阈值视图，不是能主动调度资源的预算控制器。
23. 三个参考项目已进入长期资产管理：后续吸收 `TradingAgents-astock`、`daily_stock_analysis` 或 `go-stock` 的能力时，必须更新 `docs/reference-integration-map.md`。
24. 取消不是底层线程/外部引擎的强制中断；当前公告只接入标题流，仍未实现交易所公告正文、资金流、分布式 worker、筛选分页或完整任务详情页。
25. 同花顺问财目前作为可选在线源工作，未配置 API key 时会自动退回到东财 F10 和其他在线源，不会伪造数据。
26. 研究工具入口已经开放了 `context / quote / technicals / fundamentals / news` 五类调用，同时又补齐了 `capital_flow / longhubang / unlocks` 三类薄切片，但目前还是 HTTP/Python 目录级能力，还没有把它封装成完整的多 agent 工具编排层或 MCP 风格的动态工具市场。
27. Web 工作台现在新增了研究工具调试面板，可以直接查看当前报告股票对应的原始工具返回值，但这仍是调试层能力，不是独立业务数据源。
28. 公告标题流已经升级到公告正文薄切片，`SinaBulletinProvider` 会尝试抓公告详情页正文，结构化事件抽取会直接消费正文内容，但仍不是完整公告解析引擎。
29. 研究工具调试面板里的龙虎榜摘要已经能直接看出净流入、净流出或持平，避免只读数值不看方向。
30. Web 报告详情页新增了“研究信号”摘要区，会把资金流、龙虎榜、公告线索和结构化事件压成一段和投资计划相邻的判读，帮助用户快速理解研究工具对计划的影响。
31. 研究信号摘要现在直接显示计划方向、目标仓位和止损/止盈，并判断当前研究信号和计划是否一致，形成更强的前端语义对齐。
32. `InvestmentPlan` 的理由和风险说明现在会显式回写高优先级事件的证据范围，让计划层能说明本次建议主要依赖标题、正文还是两者都命中。
33. `InvestmentPlan` 的正向证据和风险证据现在可以分别回写来源，让做多依据和防守依据不再混在同一段解释里。

离线验证命令：

```bash
PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -v
```

阶段 5.20 离线结果：`143 passed, 3 skipped`。
review 补强目标测试结果：`25 passed`。
阶段 5.21 定向验证结果：`64 passed`，`python -m compileall -q services/api/money_api` 和 `node --check apps/web/src/app.js` 通过。
阶段 5.22 定向验证结果：`65 passed`，`python -m compileall -q services/api/money_api` 和 `node --check apps/web/src/app.js` 通过。
阶段 5.23 定向验证结果：`66 passed`，`python -m compileall -q services/api/money_api` 和 `node --check apps/web/src/app.js` 通过。
阶段 5.24 定向验证结果：`67 passed`，`python -m compileall -q services/api/money_api` 和 `node --check apps/web/src/app.js` 通过。
阶段 5.25 定向验证结果：`35 passed`，`python -m compileall -q services/api/money_api` 和 `node --check apps/web/src/app.js` 通过。
阶段 5.26 定向验证结果：`49 passed`，`python -m compileall -q services/api/money_api` 和 `node --check apps/web/src/app.js && node --check apps/web/src/mockData.js` 通过。
阶段 5.27 定向验证结果：`72 passed`，`python -m compileall -q services/api/money_api` 和 `node --check apps/web/src/app.js && node --check apps/web/src/mockData.js` 通过。
阶段 5.28 定向验证结果：`74 passed`，`python -m compileall -q services/api/money_api` 和 `node --check apps/web/src/app.js && node --check apps/web/src/mockData.js` 通过。
阶段 5.29 定向验证结果：`74 passed`，`python -m compileall -q services/api/money_api` 和 `node --check apps/web/src/app.js && node --check apps/web/src/mockData.js` 通过。
阶段 5.30 定向验证结果：`74 passed`，`python -m compileall -q services/api/money_api` 和 `node --check apps/web/src/app.js && node --check apps/web/src/mockData.js` 通过。
阶段 5.31 定向验证结果：`76 passed`，`python -m compileall -q services/api/money_api` 和 `node --check apps/web/src/app.js && node --check apps/web/src/mockData.js` 通过。
阶段 5.37 定向验证结果：`29 passed`，`python -m compileall -q services/api/money_api services/api/tests` 通过，`PYTHONPATH=services/api pytest -q services/api/tests/test_analysis_service.py services/api/tests/test_analysis_api.py services/api/tests/test_web_workbench.py` 通过。
阶段 5.38 定向验证结果：`22 passed`，`python3 -m compileall -q services/api/money_api services/api/tests` 和 `PYTHONPATH=services/api pytest -q services/api/tests/test_analysis_service.py services/api/tests/test_analysis_api.py` 通过。
阶段 5.39 定向验证结果：`node --check apps/web/src/app.js` 通过。
阶段 5.40 定向验证结果：`node --check apps/web/src/app.js` 和 `node --check apps/web/src/mockData.js` 通过。
阶段 5.41 定向验证结果：`node --check apps/web/src/app.js` 通过。
阶段 5.42 定向验证结果：`node --check apps/web/src/app.js` 通过。

Sina K 线真实网络 smoke 结果：`1 passed`。

TradingAgents 真实 smoke 结果：`1 passed`。

macOS 构建结果：`apps/desktop/dist/mac-arm64/Money Never Sleep.app`。

Web 打开方式：`apps/web/index.html`。

HTTP API 模式：启动 server 后打开 `apps/web/index.html?api=http://127.0.0.1:8000`。

桌面构建命令：`cd apps/desktop && npm run build:mac`。

## 下一阶段建议

建议下一步继续扩展结构化事件流的覆盖面，例如补事件正文、更多高价值事件类型和更细的分类规则，同时把这些事件直接串到更专业的投资计划模板里。

下一阶段如果继续推进在线化，优先补资金流、龙虎榜、解禁和公告正文，再考虑把工具层做成更完整的 agent 可调用目录。

下一阶段做计划时使用当前可用最新模型；执行开发、测试和文档落地使用次一级性价比模型。计划必须显式说明借鉴三个参考项目中的哪些能力，以及哪些能力选择复制、适配或重设计。

当前计划层的最小闭环已经有了：`RiskControlPlan` 负责纪律，`InvestmentPlan` 负责执行步骤，`DataTrustScore` 负责可信度解释，`EngineTelemetry` 负责运行治理，`EngineCostGuardrail` 负责成本阈值和告警，`DataContext` / `data_sources` / `engine_mode` 负责证据和来源。事件优先级已经开始影响计划方向和仓位，结构化事件也已经能区分命中来自标题、正文还是两者，并给出原文证据片段；正文命中片段现在也能直接读懂，股东增持信号也已纳入，后续若再扩展计划层，需要新的问题域，而不是再加一次同义字段。

## 想法池

- 把 TradingAgents-astock 接成 `DeepResearchEngine` 的真实实现。
- 借鉴 daily_stock_analysis 的数据源 fallback 和报告管理。
- 借鉴 go-stock 的行情图表、桌面体验和工具分组。
- 为每次分析保存输入数据摘要，便于后续复盘和对比。
- 设计投资计划输出契约、数据可信度评分、模型/引擎成本治理和合规边界展示。
- 后续 README 可增加英文文档链接，例如 `docs/README_EN.md`。
