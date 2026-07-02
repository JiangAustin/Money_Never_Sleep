# 改进台账

状态：活文档
最近更新：2026-07-02

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
| MNS-BL-002 | 已完成 | P0 | 桌面端技术选型与 macOS 构建入口 | `apps/desktop` 仍是预留目录，没有 Electron/Tauri/Wails 配置 | 满足本地桌面体验和用户偏好的每阶段 macOS 构建验证 | 已在阶段 6 完成 Electron 桌面壳和 macOS `.app` 构建入口；验证：`72 passed, 2 skipped`，`npm audit --audit-level=high` 无漏洞，产物 `apps/desktop/dist/mac-arm64/Money Never Sleep.app` | 阶段 6、`apps/desktop/` |
| MNS-BL-015 | 待设计 | P1 | 桌面应用签名、公证、DMG 和图标 | 阶段 6 第一版只构建 `.app` 目录，避免引入证书、公证和安装包复杂度 | 提供更接近真实分发的 macOS 体验 | 准备图标和 Apple Developer 证书后，设计签名/公证/DMG 流程 | 阶段 6、`apps/desktop/` |
| MNS-BL-016 | 已完成 | P1 | 桌面内嵌或托管 Python API server | 阶段 6 默认不管理 Python 子进程，避免进程生命周期复杂度 | 桌面应用可独立发起真实分析，不要求用户手动启动后端 | 已在阶段 6.1 完成桌面托管 server、health 检查、退出清理和 API 源码打包；仍依赖本机 Python runtime | 阶段 6.1、HTTP API |
| MNS-BL-013 | 待设计 | P1 | FastAPI/OpenAPI 升级 | 阶段 5.5 为避免新增依赖，先使用标准库 HTTP dispatcher | 获得 OpenAPI、自动文档、中间件和更成熟的服务化能力 | 在桌面壳或 Web 真联调稳定后，评估将 dispatcher 外层替换为 FastAPI | 阶段 5.5、`services/api/money_api/api/http.py` |
| MNS-BL-014 | 已完成 | P1 | 异步任务队列与状态轮询 | 阶段 5.5 只做同步 HTTP 调用，避免一次性引入队列和 worker | 长耗时 TradingAgents 分析可被 Web/桌面稳定轮询和恢复 | 已在阶段 5.6 完成 in-memory task queue、`POST /tasks/analysis`、`GET /tasks/{id}` 和 Web 轮询；任务持久化/取消/恢复仍是后续项 | 阶段 5.6、`AnalysisStatus` |
| MNS-BL-003 | 已完成 | P1 | 真实 TradingAgents smoke | 阶段 3 只提供 opt-in smoke，默认测试不能依赖 LLM/API key | 验证真实多 Agent 投研链路可被 Money_Never_sleep 调起 | 已运行 `MNS_RUN_TRADINGAGENTS_SMOKE=1 ...test_tradingagents_smoke.py`，结果 `1 passed` | 阶段 3、`services/api/tests/test_tradingagents_smoke.py` |
| MNS-BL-004 | 待设计 | P1 | JSON 报告仓储升级为 SQLite 或可迁移仓储 | 阶段 4 为降低复杂度先使用 JSON 文件 | 提升查询、筛选、分页和并发写入能力 | 在 Web API 接入后评估 SQLite schema 和迁移策略 | 阶段 4、`report_repository.py` |
| MNS-BL-005 | 已完成 | P1 | 真实 K 线、技术指标和估值扩展 | 阶段 2 只接入腾讯 quote 最小真实路径 | 提高深度分析上下文质量，减少 mock/fixture 依赖 | 已在阶段 5.32 完成 runtime provider bundle：腾讯 quote、Sina K 线技术指标、东财 F10 基本面和可选同花顺问财；验证：compileall + 在线 smoke | 阶段 2/5.32、`domains/market_data/` |
| MNS-BL-006 | 进行中 | P1 | 新闻、公告、资金流、龙虎榜和解禁 provider | 阶段 2 明确不接宽数据面 | 支撑 A 股政策、游资、解禁等 TradingAgents 角色 | 新闻、市场快讯、公告标题和在线基本面/技术面已接入；研究工具目录已补齐资金流、龙虎榜和解禁三类薄切片；结构化事件第一切片已扩展到回购/质押/增持等高价值事件，并新增优先级、证据范围和证据片段字段且已影响计划方向；下一步继续补公告正文 | 阶段 2/3、TradingAgents-astock 参考 |
| MNS-BL-007 | 已完成 | P1 | 分析任务持久化与恢复 | 当前阶段 5.6 已有内存队列和状态轮询，但任务生命周期不持久 | 支持服务重启后恢复、历史任务查询、取消与重试 | 已在阶段 5.7 完成 JSON task repository、`GET /tasks` 和中断任务恢复为 failed；取消与重试仍是后续项 | 阶段 5.7、`AnalysisStatus` |
| MNS-BL-008 | 待设计 | P2 | 报告追问与分析会话 | 阶段 4 只保存最终报告，没有 conversation/session | 支持围绕历史报告继续提问、补证据、复盘 | 在报告持久化稳定后设计 `AnalysisSession` 和追问记录 | 阶段 4/5 |
| MNS-BL-009 | 待设计 | P2 | 投资免责声明与风险提示治理 | 当前有风险字段，但没有统一产品级免责声明 | 降低误解为自动荐股的风险，统一 Web/API/报告表达 | 增加 report disclaimer 字段或 UI 固定风险说明 | README、Web、报告契约 |
| MNS-BL-017 | 已完成 | P0 | 风控纪律层 | 此前报告只有 action/confidence/risks，没有统一仓位、止损、止盈和免责声明 | 让每份报告都有可复盘的纪律约束，避免只输出买卖结论 | 已在阶段 7 完成 `RiskControlPlan`、默认风险策略、Service/API 集成和 Web mock 兼容；验证：`79 passed, 2 skipped`，macOS `.app` 构建通过 | 阶段 7、`AnalysisReport` |
| MNS-BL-018 | 已完成 | P1 | 回测接口 | 阶段 7 第一版先做风控纪律，不做历史行情回放和收益归因 | 验证建议是否能被历史数据复盘，而不是只看当下结论 | 已在阶段 7.1 完成基于传入价格序列的 deterministic backtest request/result、Python API 和 HTTP API；验证：`87 passed, 2 skipped`，macOS `.app` 构建通过 | 阶段 7.1 |
| MNS-BL-020 | 已完成 | P1 | 真实行情回测数据源 | 阶段 7.1 只接受调用者传入价格序列，不接真实 K 线 provider | 回测可以直接基于真实历史行情运行，减少手工输入 | 已在阶段 7.2 完成 Sina 日线 K 线 provider 和 provider 回测 API；验证：`93 passed, 3 skipped`，macOS `.app` 构建通过 | 阶段 7.2、`domains/market_data/` |
| MNS-BL-022 | 已完成 | P1 | Sina K 线真实网络 smoke | 阶段 7.2 先做离线 parser/provider 测试，避免默认测试依赖外网 | 验证 Sina 当前真实接口能返回可用于回测的价格序列 | 已新增 opt-in smoke：默认 skip；`MNS_RUN_NETWORK_SMOKE=1 ...test_sina_kline_smoke.py` 验证 `1 passed` | 阶段 7.2、`services/api/tests/test_sina_kline_smoke.py` |
| MNS-BL-023 | 已完成 | P1 | 桌面启动诊断 | 阶段 6.1 虽已托管本地 API，但失败回退对用户不可见 | 让用户知道当前是托管 API、外部 API 还是离线模式，并看到最近错误 | 已在阶段 6.2 完成 startup 上下文注入、mode pill 和诊断面板启动区块；验证：`107 passed, 3 skipped` | 阶段 6.2、`apps/desktop/src/main.js`、`apps/web/src/app.js` |
| MNS-BL-024 | 已完成 | P1 | HTTP 分析任务队列 | 阶段 5.5 只有同步 `POST /analysis`，真实深度分析会变成长请求 | 让 Web/桌面可以稳定轮询长任务并在完成后拉报告 | 已在阶段 5.6 完成任务创建、状态轮询和 Web 接入；验证：`110 passed, 3 skipped` | 阶段 5.6、`services/api/money_api/api/http.py`、`apps/web/src/app.js` |
| MNS-BL-025 | 已完成 | P1 | 任务历史查询与重启恢复 | 阶段 5.6 任务全在内存中，服务重启后任务上下文会丢失 | 让近期任务可查询，并让中断任务有明确失败状态 | 已在阶段 5.7 完成 JSON task repository、`GET /tasks` 和中断任务恢复标记；验证：`115 passed, 3 skipped` | 阶段 5.7、`services/api/money_api/domains/analysis/task_queue.py` |
| MNS-BL-026 | 已完成 | P1 | 任务取消与重试控制 | 阶段 5.7 任务可查询但不可控，用户无法取消长任务或基于失败任务重跑 | 为真实深度分析链路提供最小控制面 | 已在阶段 5.8 完成 cancel/retry 端点和 cancelled 状态；验证：`119 passed, 3 skipped` | 阶段 5.8、`services/api/money_api/domains/analysis/task_queue.py` |
| MNS-BL-027 | 已完成 | P1 | 任务超时回收 | 阶段 5.8 已能取消与重试，但卡住任务仍可能无限轮询 | 让长任务在没有人工介入时也能收敛为明确失败状态 | 已在阶段 5.9 完成 `timeout_s`、`started_at` 和读取路径上的超时失败标记；验证：`122 passed, 3 skipped` | 阶段 5.9、`services/api/money_api/domains/analysis/task_queue.py` |
| MNS-BL-029 | 已完成 | P1 | Web 任务控制入口 | 阶段 5.8-5.10 已有服务端控制语义，但用户仍需手工调用 API | 让真实 API 模式下的任务控制真正可用 | 已在阶段 5.11 完成取消/重试按钮和前端状态跟踪；验证：`125 passed, 3 skipped` | 阶段 5.11、`apps/web/src/app.js` |
| MNS-BL-028 | 已完成 | P1 | 任务 watchdog 与自动重试 | 阶段 5.9 的超时回收仍依赖读取路径，失败任务也需人工重试 | 让后台可主动收敛超时任务，并降低偶发失败的人肉介入成本 | 已在阶段 5.10 完成 watchdog 扫描、`max_retries` 和 `retry_count`；验证：`125 passed, 3 skipped` | 阶段 5.10、`services/api/money_api/domains/analysis/task_queue.py` |
| MNS-BL-030 | 已完成 | P1 | Web 任务历史视图 | 阶段 5.11 用户只能控制当前任务，看不到近期任务状态 | 让真实 API 模式下的任务结果和失败原因更可见 | 已在阶段 5.12 完成最近任务列表和任务操作后的刷新；验证：`125 passed, 3 skipped` | 阶段 5.12、`apps/web/src/app.js` |
| MNS-BL-031 | 已完成 | P1 | 任务重试退避调度 | 阶段 5.10 自动重试是立即触发，无法体现“何时重试”且容易在瞬时故障下快速耗尽重试次数 | 让失败任务进入可解释的计划重试状态，并在 watchdog 到点后再派生重试任务 | 已在阶段 5.13 完成 `next_retry_at`、指数退避调度和到点派生重试；验证：`126 passed, 3 skipped` | 阶段 5.13、`services/api/money_api/domains/analysis/task_queue.py` |
| MNS-BL-032 | 已完成 | P1 | 任务重试策略细化（抖动+超时倍率） | 阶段 5.13 仅有固定指数退避，缺少错误类型差异和抖动能力 | 减少同秒重试集中，并让 timeout 类故障应用更保守重试间隔 | 已在阶段 5.14 完成 `retry_backoff_factor`、`retry_jitter_ratio`、`retry_timeout_multiplier`；验证：`127 passed, 3 skipped` | 阶段 5.14、`services/api/money_api/domains/analysis/task_queue.py` |
| MNS-BL-033 | 已完成 | P1 | 任务重试策略可观测性 | 阶段 5.14 的策略虽已可配置，但调用方只能看到 `next_retry_at`，无法判断延迟来源与命中的策略 | 让任务历史和 API 能解释“为什么这次要等这么久” | 已在阶段 5.15 完成 `next_retry_delay_s`、`next_retry_policy` 和 Web 历史展示；验证：`128 passed, 3 skipped` | 阶段 5.15、`services/api/money_api/domains/analysis/task_queue.py`、`apps/web/src/app.js` |
| MNS-BL-034 | 已完成 | P1 | 真实个股新闻数据接入 | runtime service 只有 quote 是真实输入，news 仍是静态示例数据 | 让分析上下文开始具备真实资讯时效性，为后续真实多 Agent 分析提供更可信输入 | 已在阶段 5.16 完成 `EastmoneyNewsProvider` 和 runtime news 装配；验证：`131 passed, 3 skipped` | 阶段 5.16、`services/api/money_api/domains/market_data/eastmoney_news.py` |
| MNS-BL-035 | 已完成 | P1 | runtime 默认深度引擎 auto 模式 | 虽已具备真实 TradingAgents 集成边界，但默认路径仍固定 mock，无法优先尝试真实引擎 | 让默认链路在环境就绪时优先走真实 TradingAgents，同时保留安全回退 | 已在阶段 5.17 完成 `AutoFallbackDeepResearchEngine`、runtime/desktop 默认 `auto` 和 runner 路径引导；验证：`133 passed, 3 skipped` | 阶段 5.17、`services/api/money_api/domains/analysis/tradingagents_engine.py` |
| MNS-BL-036 | 已完成 | P1 | runtime 市场快讯接入 | 默认 news 上下文只有个股新闻，缺少政策、情绪与突发事件层输入 | 让默认分析上下文同时覆盖个股与市场层资讯，提升真实 TradingAgents 的输入广度 | 已在阶段 5.18 完成 `ClsMarketFlashProvider`、`CompositeNewsProvider` 和 runtime news 合并；验证：`137 passed, 3 skipped` | 阶段 5.18、`services/api/money_api/domains/market_data/cls_market_flash.py` |
| MNS-BL-037 | 已完成 | P1 | runtime 公司公告标题流接入 | 默认 news 上下文已有个股新闻和市场快讯，但缺少公司正式公告标题 | 让默认分析上下文覆盖更接近公司事件面的正式公告流，为后续事件分类与结构化公告打基础 | 已在阶段 5.19 完成 `SinaBulletinProvider` 和 runtime news 合并；验证：`140 passed, 3 skipped` | 阶段 5.19、`services/api/money_api/domains/market_data/sina_bulletin.py` |
| MNS-BL-038 | 已完成 | P1 | 结构化事件流 | 当前已接入个股新闻、市场快讯和公告标题，但公司事件仍停留在标题/摘要层，TradingAgents 无法直接消费“业绩预告/担保/减持/解禁”的结构化字段 | 让默认分析上下文从资讯层提升到事件层，为真实投研和风险分析提供更高信噪比输入 | 已完成 `MarketEvent` 契约、关键词分类器、`DataContext.events` 和 Web/报告展示；验证：`143 passed, 3 skipped` | 阶段 5.20、`services/api/money_api/domains/analysis/` |
| MNS-BL-039 | 已完成 | P1 | auto 模式前端可见性 | 虽然默认 deep engine 已是 `auto`，但当前用户从 Web/桌面界面无法直接判断这次分析究竟命中了真实 TradingAgents 还是回退到了 mock | 减少“看起来像真实分析其实已回退”的误解，便于后续问题定位和产品验收 | 已完成 `data_sources` / `engine_source` / `engine_mode` / `fallback_reason` 展示和诊断面板渲染；验证：`143 passed, 3 skipped` | 阶段 5.20、`apps/web/src/app.js` |
| MNS-BL-040 | 已完成 | P1 | 结构化事件兼容性修复 | review 发现未知 `event_type` 会导致反序列化异常，且单条标题同时命中多类事件时只保留第一类 | 提高事件契约前向兼容性，避免旧报告/新事件类型破坏读取，并减少事件漏报 | 已完成未知类型降级为 `other`、单条资讯多事件输出、旧 JSON 报告列表 provenance 回填；验证：目标测试 `25 passed` | 阶段 5.20 review、`contracts.py`、`market_events.py`、`report_repository.py` |
| MNS-BL-041 | 已完成 | P1 | 投资计划输出契约 | 当前报告已有 action、confidence、risk plan，但还不是专业基金经理式的完整执行计划 | 让建议从“方向判断”升级为“可跟踪计划”，包含买入条件、仓位、卖出条件、止损、止盈、观察窗口和复盘条件 | 已完成 `InvestmentPlan` 契约、报告序列化、服务端自动生成和 Web 展示；验证：定向测试 `64 passed` | 阶段 5.20 后续、`docs/reference-integration-map.md` |
| MNS-BL-042 | 已完成 | P1 | 数据可信度评分 | 当前 diagnostics 和 gaps 可见，但缺少统一可信度评分和结论置信来源解释 | 用户能区分真实数据、fallback、过期数据、缺失数据和真实引擎是否消费过证据 | 已完成 `DataTrustScore` 契约、评分逻辑、报告序列化、服务端自动生成和 Web 展示；验证：定向测试 `65 passed` | 数据层、报告契约 |
| MNS-BL-043 | 已完成 | P1 | 模型/引擎成本与失败治理 | `auto` 已显示命中与回退，但此前尚未记录成本、耗时、调用次数和失败类型 | 控制真实 TradingAgents/LLM 成本，避免长周期使用时失控 | 已完成 `EngineTelemetry`、`EngineCostGuardrail`、成本阈值、告警和预算限制的第一版运行治理；验证：定向测试 `67 passed` | TradingAgents adapter、任务队列 |
| MNS-BL-044 | 已完成 | P1 | 参考项目能力矩阵 | 此前只在交接文档零散提到三个参考项目，缺少长期跟踪位置 | 防止后续压缩记忆后遗失“可借鉴、可复制、需重设计”的资产判断 | 已新增 `docs/reference-integration-map.md`，并把写回规则补入信息地图和全局规则 | `docs/reference-integration-map.md` |
| MNS-BL-045 | 已完成 | P1 | 研究工具 API | 之前只有整份分析报告和少量 Python wrapper，没有面向 agent 的细粒度研究入口 | 让外部 agent 或上层工作流可以按 `context / quote / technicals / fundamentals / news` 直接取在线研究数据 | 已完成 `ResearchToolService` 和 HTTP `/research/*` 入口；验证：compileall + smoke | `services/api/money_api/domains/analysis/research_tools.py`、`services/api/money_api/api/http.py` |
| MNS-BL-046 | 已完成 | P1 | 研究工具薄切片扩展 | 研究工具 API 第一版只覆盖上下文、行情、技术面、基本面和新闻 | 让外部 agent 或上层工作流可以继续按资金流、龙虎榜和解禁粒度直接查数据 | 已完成 `capital_flow / longhubang / unlocks` 三类入口；验证：compileall + smoke | `services/api/money_api/domains/analysis/research_tools.py`、`services/api/money_api/api/http.py` |
| MNS-BL-047 | 已完成 | P2 | Web 研究工具调试面板 | 研究工具 API 已有，但 Web 端仍只能看整份报告，无法直接检查工具返回值 | 让用户和 agent 能在浏览器里直接验证 provider 返回、回退语义和数据缺口 | 已完成诊断区调试面板，自动拉取 `context / quote / technicals / fundamentals / news / capital-flow / longhubang / unlocks`；验证：`12 passed`、compileall、`node --check apps/web/src/app.js` | `apps/web/src/app.js`、`docs/decision-log.md` |
| MNS-BL-048 | 已完成 | P1 | 公告正文薄切片 | 研究工具和事件流已经接了公告标题，但正文里往往才有真正的信号 | 先用最小代价把公告正文接进同一条 `news`/`events` 管线，提高结构化事件命中质量 | 已完成 `SinaBulletinProvider` 正文抓取与清洗；验证：`27 passed`、compileall、`node --check apps/web/src/app.js` | `services/api/money_api/domains/market_data/sina_bulletin.py`、`services/api/tests/test_sina_bulletin.py` |
| MNS-BL-049 | 已完成 | P2 | 研究信号联动摘要 | 调试面板能看原始数据，但用户还需要一眼知道这些信号对计划意味着什么 | 把资金流、龙虎榜、公告线索和结构化事件压成与投资计划相邻的判读 | 已完成 Web 报告详情页“研究信号”摘要区；验证：`27 passed`、compileall、`node --check apps/web/src/app.js` | `apps/web/src/app.js`、`docs/decision-log.md` |
| MNS-BL-050 | 已完成 | P2 | 研究信号与计划对齐 | 只有研究信号摘要还不够，用户还需要知道它和当前投资计划是否一致 | 直接显示计划方向、目标仓位和止损/止盈，并给出一致/分歧判读 | 已完成前端对齐文案；验证：`27 passed`、compileall、`node --check apps/web/src/app.js` | `apps/web/src/app.js`、`docs/decision-log.md` |
| MNS-BL-051 | 已完成 | P2 | 投资计划证据范围回写 | 计划层已经有方向、仓位和对齐判读，但还缺少“这次建议主要基于什么证据”的显式说明 | 让 `InvestmentPlan` 的理由和风险说明可以直接看出标题、正文或两者都命中 | 已完成后端计划解释回写与测试补强；验证：`29 passed`、compileall | `services/api/money_api/domains/analysis/service.py`、`docs/decision-log.md` |
| MNS-BL-052 | 已完成 | P2 | 投资计划正负证据拆线 | 只有总证据范围还不够，正向依据和风险依据仍然混在同一条解释里 | 让 `InvestmentPlan` 分别展示做多依据和防守依据的标题/正文命中来源 | 已完成正向/风险证据拆线与测试补强；验证：compileall + pytest | `services/api/money_api/domains/analysis/service.py`、`docs/decision-log.md` |
| MNS-BL-021 | 已完成 | P2 | 交易成本、滑点和复权参数 | 阶段 7.1 为保持 deterministic 最小闭环，不做成本和复权 | 提高回测结果可信度，避免过度乐观 | 已在阶段 7.4 完成 `BacktestOptions`、净收益/裸收益/成本影响和 Python/HTTP API 参数；真实复权价格转换仍是后续项 | 阶段 7.4 |
| MNS-BL-019 | 已完成 | P1 | 组合风险预算 | 当前系统仍是单股分析，没有组合层持仓和风险预算 | 支持多标的仓位约束、集中度控制和组合视图 | 已在阶段 7.3 完成组合预算契约、预算器、Python API 和 HTTP API；验证：`100 passed, 3 skipped` | 阶段 7.3 |
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

- Web 是零依赖静态版本，默认使用离线 mock 数据。
- 阶段 5.20 已支持 `?api=` HTTP 任务模式、任务持久化、cancel/retry、超时回收、带延迟退避的服务端自动重试和最近任务历史，接入真实个股新闻、CLS 市场快讯、公司公告标题、结构化事件第一切片，并让默认深度引擎进入 `auto` 模式；但仍未提供交易所公告正文/资金流、筛选分页、批量控制和完整任务详情页。
- 如果继续沿当前主线推进，下一优先级不是再加一个通用页面，而是把结构化事件流扩成更完整的正文/分类/优先级体系，再考虑资金流和龙虎榜。
- 未引入前端框架、路由、状态管理、图表或自动化浏览器截图验证。

### 阶段 6：桌面端与本地体验

- 已选择 Electron 并补齐 macOS `.app` 构建入口。
- 已支持桌面托管本地 Python API server 和启动诊断，但仍未签名、公证、打 DMG、设置图标，也未随应用打包 Python runtime。

### 阶段 7：风控、回测与组合

- 风控纪律层已完成第一版。
- 回测接口、组合风险预算、绩效归因和交易执行尚未实现。

## 后续 agent 操作清单

开始新阶段或新任务前：

1. 读取 `docs/information-map.md` 确认信息入口和写回位置。
2. 读取 `docs/stages.md` 确认当前阶段状态。
3. 读取本文件确认未完成事项和优先级。
4. 读取 `docs/agent-handoff.md` 理解已完成架构、关键取舍和验证方式。
5. 如果新增或推迟任何事项，先更新本文件，再进入实现计划或在任务收尾时补齐。
