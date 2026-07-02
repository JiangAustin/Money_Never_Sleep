# Agent 交接说明

状态：活文档
最近更新：2026-07-03

本文档给后续 agent 或模型快速理解 Money_Never_sleep 已做什么、为什么这么做、收益是什么、哪些没做、下一步怎么接。它不是阶段计划的替代品；如果你刚接手，先读 `docs/information-map.md`，再读本文档。详细阶段状态看 `docs/stages.md`，未完成事项看 `docs/improvement-backlog.md`。

## 最近连续推进摘要

最近一轮工作重点不是新建大模块，而是把默认 runtime 路径从“半真实原型”连续推进到“真实输入优先、真实深度分析优先尝试”的状态。已经连续完成：

1. 阶段 5.16：接入东方财富个股新闻，默认 runtime 不再只用静态示例新闻。
2. 阶段 5.17：默认深度引擎切到 `auto`，优先尝试真实 TradingAgents，失败自动回退 mock。
3. 阶段 5.18：接入 CLS 市场快讯，默认 `news` 从个股层扩到市场层。
4. 阶段 5.19：接入新浪公告标题流，默认 `news` 继续扩到公司正式公告层。

因此，当前默认 runtime 的真实输入面已经从单一 quote 扩展为：

- 腾讯 quote
- Sina K 线技术指标
- 东方财富 F10 基本面
- 东方财富个股新闻
- CLS 市场快讯
- 新浪公告标题
- `auto` 深度引擎（优先 TradingAgents，失败回退工具驱动分析）

最近又补了一层在线工具化数据层和研究工具入口：

- `MONEY_MARKET_DATA_MODE=tencent` / `online` 下，默认 runtime 现在会同时拉腾讯 quote、Sina K 线、东财 F10 基本面和合并新闻流，不再依赖静态 fixture 当默认输入。
- 同花顺问财被接成可选在线源；如果未配置 API key，系统会自动退回东财 F10 和其他在线源，不会伪造基本面数据。
- `auto` 回退不再直接掉到 mock，而是先给出工具驱动报告，至少保证“真实数据 + 规则化解释”的可用闭环。
- 研究工具目录已经开放为 `context / quote / technicals / fundamentals / news` 五类 HTTP/Python 调用，方便 agent 直接取研究数据，不必先跑整份分析报告。
- 后来又补了资金流、龙虎榜和解禁三个薄切片工具入口，继续把“可直接用”的粒度往前推。
- Web 工作台现在也接上了“研究工具调试”面板，会按当前报告股票自动拉取这些工具的原始返回值，方便直接看 provider 结果而不是只看整份报告。
- 公告标题流现在也被薄切片升级成了公告正文可读层，`SinaBulletinProvider` 会尝试抓公告详情页正文，结构化事件抽取会直接消费正文内容。
- 资金流、龙虎榜和解禁的 Web 调试展示已经补了摘要层，会直接显示主力净流入、龙虎榜净额和解禁规模，方便快速扫读。
- 龙虎榜摘要现在还会显式标出净流入、净流出或持平，减少只看数字时的误判。
- Web 报告详情页新增了“研究信号”摘要区，会把资金流、龙虎榜、公告线索和结构化事件压成一段和投资计划相邻的判读。
- 研究信号摘要现在会直接显示计划方向、目标仓位和止损/止盈，并判断当前研究信号和计划是否一致。
- `InvestmentPlan` 的理由和风险说明现在也会回写证据范围，明确这次建议主要依赖标题、正文还是两者都命中，避免计划层继续显得像黑箱。
- `InvestmentPlan` 的证据回写现在进一步拆成正向证据和风险证据两条线，分别标明做多依据和防守依据来自标题、正文还是两者都命中。
- Web 报告详情页的投资计划区块现在也显示一个轻量“证据来源”小节，避免用户只看理由和风险备注还要去研究信号区猜来源。
- 报告列表页现在也会展示一行证据摘要，帮助用户在进入详情前先判断计划是偏正向还是偏风险。
- 任务历史现在也会复用报告证据摘要，避免异步任务链路只显示状态不显示方向。
- `auto` 回退在 Web 详情页现在会给出可读提示，能直接分辨是凭据缺失还是运行失败导致回退。
- 任务历史现在支持状态筛选和单条任务详情卡，能直接看任务时间、重试信息、错误和证据摘要。

如果下一个 agent 只想快速判断“现在系统最像什么”，答案是：

默认链路已经具备“真实行情 + 真实技术指标 + 真实基本面 + 真实资讯/公告输入 + 真实深度引擎优先尝试”的产品雏形，并且已经有了第一版结构化事件流与引擎 provenance 展示；但事件覆盖面仍只停留在标题/摘要级的薄切片，后续还要继续扩展。
Web 端已经能直接查看研究工具原始返回值，但这只是调试面板，不是新的数据源或独立业务层。
公告正文已经进入同一条 `news` / `events` 管线，但仍是薄切片正文抓取，不是完整公告解析引擎。
研究工具调试面板现在对资金流、龙虎榜和解禁提供摘要视图，但它仍然只是诊断层，真正的业务层建议还没把这些信号直接纳入计划逻辑。
龙虎榜当前只是方向和规模的摘要展示，仍不是完整的榜单分析器。
研究信号摘要是前端判读层，不是新增的分析契约；它依赖研究工具调试结果和当前报告上下文。
研究信号摘要现在已经和 `InvestmentPlan` 对齐，但仍然只是前端表达层，后端计划生成逻辑还没有因此改写。
投资计划层现在补上了证据范围回写，但仍是规则化解释，不是学习型计划引擎。
投资计划层现在又把正负证据拆线，但仍是解释增强，不是新的计划模型。
Web 展示也补上了这条解释链，但仍保持轻量，不是独立分析面板。
列表页也补上了最小摘要，但仍然只是扫读信息，不是完整解释面板。
任务历史也只补最小摘要，不单独做第二个详情面板。
`auto` 回退提示也保持在详情页里，不扩成新面板或独立告警系统。
任务历史筛选也只是轻量工作台增强，不会变成独立的任务管理页面。

这次在线化实现借鉴的参考项目能力很明确：

- `TradingAgents-astock`：借鉴多 agent 投研分工、工具调用约定和深度分析角色结构。
- `daily_stock_analysis`：借鉴 fail-open provider 编排、报告可追溯性和日常可运行的工程边界。
- `go-stock`：借鉴 Eastmoney F10 / iWenCai / 工具分组的接口组织方式，主要复制的是工具目录和数据入口形状，不复制 Go 侧实现。

最近 review 已采纳并完成三项补强：

1. `MarketEvent.from_dict()` 对未知 `event_type` 安全降级为 `other`，避免未来事件类型破坏旧读取路径。
2. 结构化事件分类器支持单条资讯命中多类事件，不再只保留第一类。
3. 旧 JSON 报告列表如果顶层缺少 provenance，会从内层 `report` 回填 `data_sources`、`engine_source`、`engine_mode` 和 `fallback_reason`。

随后又补了一层第一版投资计划：

- `AnalysisReport` 新增 `investment_plan`，由 `AnalysisService` 基于最终报告和风控结果生成。
- Web 详情页和 mock 数据也同步显示入场条件、退出条件、复核条件和观察窗口。
- 目前它仍是规则化生成，不是独立优化器，但已经能作为“基金经理式计划层”的稳定入口。

随后又补了一层数据可信度：

- `AnalysisReport` 新增 `data_trust`，由 `AnalysisService` 基于 `data_sources`、`gaps`、`diagnostics` 和回退信息自动生成。
- Web 详情页和 mock 数据同步显示可信度分数、等级、正向信号、扣分项和诊断元数据。
- 这层的目的不是精确建模，而是让用户一眼知道“这份建议依赖的数据到底有多可靠”。

随后又补了一层引擎运行画像：

- `AnalysisReport` 新增 `engine_telemetry`，由 `AnalysisService` 记录运行时长、执行路径、请求次数、成本层级和失败信息。
- Web 详情页和 mock 数据同步显示这份运行画像，方便区分快速轻量分析、真实深度引擎和回退路径。
- 这层不是成本预算器，只是把“本次引擎到底花了什么代价、走了哪条路”固定成可读字段。

随后又补了一层引擎成本治理：

- `AnalysisReport` 新增 `engine_cost_guardrail`，由 `AnalysisService` 基于 `engine_telemetry` 自动生成成本阈值、告警和预算命中情况。
- Web 详情页和 mock 数据同步显示这份治理信息，方便一眼判断本次分析有没有超出预设预算边界。
- 这层仍然是报告级规则视图，不是资源调度器，但已经把“成本超不超、告警是什么、怎么收口”固定成可读字段。

随后又扩了一层结构化事件覆盖：

- 现有事件切片不再只停留在业绩预告、减持、担保和解禁，还补进了股份回购与股权质押两类更高价值的 A 股事件。
- Web 离线 mock 也同步补了这两类事件，避免前端仍然只展示老样例。
- 这一层的目标不是做完整事件抽取，而是继续扩大“事件层输入”对投研建议的实际帮助。

随后又给结构化事件补上优先级：

- 事件契约新增 `priority`，让回购、质押、业绩预告等事件可以直接标记高优先级。
- Web 事件卡片会把优先级展示出来，后续计划层可以更容易按信号强弱排序。
- 这一层仍然是规则映射，不是学习型评分，但足够支撑第一版的事件排序和解释。

随后又把优先级接进投资计划生成：

- `AnalysisService` 会根据高优先级正向和风险事件，调整 `InvestmentPlan` 的方向和仓位。
- 深度分析路径下，正向事件占优时会把 `watch` 推向 `buy`；风险事件占优时会把计划收缩到 `wait`。
- 轻量查询仍保持原样，不会因为标题里有事件就自动变成荐股结果。

随后又补了结构化事件的证据范围：

- `MarketEvent` 新增 `evidence_scope`，可以标出命中来自标题、正文还是两者都命中。
- 这个字段让后续阅读报告时更容易判断事件是“标题就足够明确”还是“主要依赖正文信息”。
- 这一层仍然是解释性增强，不是额外评分系统。

随后又补了结构化事件的证据片段：

- `MarketEvent` 新增 `evidence_excerpt`，可以直接显示命中的标题或正文片段。
- 这让用户不必回头翻原文，也能直接看到为什么这条事件被抽出来。
- 这一层仍然保持在解释性范畴，没有引入新的评分或排序模型。

随后又把正文片段展示做得更可读：

- 正文命中的片段现在会直接在事件卡片里显示，方便快速扫读。
- 这样一来，标题命中和正文命中都能被肉眼理解，不需要再回到原始公告或新闻正文。
- 这层的目标仍然是解释性，不是增加新的事件评分体系。

随后又补进了股东增持信号：

- `MarketEventType` 新增 `SHARE_INCREASE`，让增持可以作为高优先级正向事件进入计划推导。
- 这个事件类型会在 Web mock 和抽取测试中显式出现，确保正向信号不是只停留在抽象层。
- 这一层继续沿用现有规则体系，没有引入额外学习模型。

## 建议接手顺序

如果继续沿最近的路线推进，推荐按下面顺序做，而不是再回到宽泛探索：

1. 继续扩结构化事件流：把当前标题级事件切片扩成更完整的正文/分类/筛选能力。
2. 再把事件流接到更明确的建议模板和组合层计划里，让事件直接影响投资计划而不是只做展示。
3. 最后再考虑更重的扩展：资金流、龙虎榜、公告正文原文抓取、结构化事件分类和更细的事件优先级。

这样做的原因：当前最缺的不是更多基础框架，而是让真实输入质量继续提升，并让“真实优先”路径对用户可见。

## 接手导航

后续 agent 或模型变更后，推荐先读：

1. `docs/information-map.md`：知道去哪里找什么、做完后写回哪里。
2. `README.md`：了解项目定位和当前能力。
3. `docs/stages.md`：确认当前阶段和下一阶段建议。
4. `docs/improvement-backlog.md`：确认第一版未做事项和优先级。
5. 本文档：理解阶段 0-5 已完成内容、设计取舍、收益和限制。
6. `docs/reference-integration-map.md`：确认三个参考项目的可借鉴能力、当前接入状态和下一步。

如果你的目标是继续默认 runtime 能力，而不是做全新模块，优先直接跳到本文档中的“最近连续推进摘要”和阶段 5.16-5.20、6.1-6.2 部分，不必先从阶段 0 重新读到尾。

## 项目方向

Money_Never_sleep 选择“自建平台骨架 + 外部项目能力吸收”的路线：

- 不直接 fork `TradingAgents-astock`、`daily_stock_analysis` 或 `go-stock`。
- Money_Never_sleep 保持自己的领域模型、API 契约、数据契约和客户端边界。
- `TradingAgents-astock` 作为深度 AI 投研引擎参考和可选真实 runner。
- `daily_stock_analysis` 作为 API、报告、数据 fallback、Web/Desktop 工程参考。
- `go-stock` 作为桌面体验、行情图表、工具分组参考。

这样做的好处：长期边界更清楚，避免多个项目技术栈硬耦合；后续可以逐步接入真实引擎、数据源、Web、桌面、回测和组合能力。

参考项目不是一次性调研材料，而是长期架构资产。后续计划必须记录借鉴来源、复制/适配范围、重设计原因和验证口径；具体跟踪位置是 `docs/reference-integration-map.md`。

模型使用规则：计划、架构取舍、复杂 review 默认使用当前可用最新模型；执行开发、测试和文档落地默认使用次一级性价比模型，除非遇到复杂调试、重大重构或高风险金融判断。

当前计划层的最小闭环已经有了：`RiskControlPlan` 负责纪律，`InvestmentPlan` 负责执行步骤，`DataTrustScore` 负责可信度解释，`EngineTelemetry` 负责运行治理，`EngineCostGuardrail` 负责成本阈值和告警，`DataContext` / `data_sources` / `engine_mode` 负责证据和来源。事件优先级已经能影响计划方向和仓位，结构化事件也开始区分标题/正文证据并给出原文片段，正文片段现在也更容易直接阅读，股东增持信号也已纳入；后续扩展时要继续围绕“能否改变决策”来判断是否值得加字段。

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

### 阶段 5.13：任务重试退避调度

做了什么：为任务记录增加 `next_retry_at`，自动重试从“失败即刻派生”改为“先计划、后到点派生”，并通过 watchdog 扫描触发到点重试。

为什么这么做：阶段 5.10 的立即重试在瞬时故障下会快速消耗重试次数，也无法让用户理解下一次重试时机。

收益：失败任务进入可解释的计划重试状态，系统具备最小指数退避能力，同时保持现有任务 API 契约兼容。

关键文件：

- `services/api/money_api/domains/analysis/task_queue.py`
- `services/api/tests/test_task_queue.py`
- `docs/stages.md`

已验证事项：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -q` 结果 `126 passed, 3 skipped`。

未做事项：当前退避策略无抖动、无按错误类型区分策略、无策略可配置化。

### 阶段 5.14：任务重试策略细化

做了什么：在任务队列引入 `retry_backoff_factor`、`retry_jitter_ratio` 和 `retry_timeout_multiplier`，让 `next_retry_at` 计算支持抖动和 timeout 错误倍率。

为什么这么做：阶段 5.13 虽解决了“立即重试”问题，但所有错误仍使用同一延迟策略，且缺少抖动，容易形成同秒重试聚集。

收益：重试调度更稳健，timeout 类故障可自动采用更保守的重试间隔，同时默认配置保持兼容。

关键文件：

- `services/api/money_api/domains/analysis/task_queue.py`
- `services/api/tests/test_task_queue.py`
- `docs/stages.md`

已验证事项：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -q` 结果 `127 passed, 3 skipped`。

未做事项：策略命中信息尚未通过 API 暴露给前端（例如 delay 来源、倍率命中、抖动值）。

### 阶段 5.15：任务重试策略可观测性

做了什么：为任务记录增加 `next_retry_delay_s` 和 `next_retry_policy`，让 `/tasks`、`/tasks/{id}` 以及 Web 最近任务列表都能看到计划重试的延迟和命中策略。

为什么这么做：阶段 5.14 已支持重试策略细化，但调用方仍无法解释 `next_retry_at` 是怎么来的。

收益：任务历史从“能看到什么时候重试”提升到“能看到为什么这样重试”，后续做筛选、详情页或诊断面板时有稳定字段可用。

关键文件：

- `services/api/money_api/domains/analysis/task_queue.py`
- `services/api/tests/test_http_api.py`
- `apps/web/src/app.js`

已验证事项：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -q` 结果 `128 passed, 3 skipped`。

未做事项：当前只暴露最终延迟秒数和策略标签，尚未暴露更细粒度的抖动值或原始基线值。

### 阶段 5.16：真实个股新闻数据接入

做了什么：新增 `EastmoneyNewsProvider`，并让 runtime service 在 `MONEY_MARKET_DATA_MODE=tencent` 时使用腾讯 quote + 东方财富个股新闻的组合输入。

为什么这么做：此前 runtime 分析虽然有真实行情，但新闻仍是静态示例，导致分析上下文的时效性和可信度不足。

收益：系统开始消费真实新闻流，Web/Desktop/HTTP API 读取到的报告上下文不再只依赖静态占位新闻，为后续接公告、快讯和真实 TradingAgents 默认链路打基础。

关键文件：

- `services/api/money_api/domains/market_data/eastmoney_news.py`
- `services/api/money_api/api/v1/router.py`
- `services/api/tests/test_eastmoney_news.py`

已验证事项：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -q` 结果 `131 passed, 3 skipped`。

未做事项：当前只接入个股新闻，不含公告、市场快讯、资金流或新闻相关性排序。

### 阶段 5.17：runtime 默认深度引擎 auto 模式

做了什么：新增 `AutoFallbackDeepResearchEngine`，让 runtime 默认 `MONEY_DEEP_ENGINE=auto` 时优先尝试真实 TradingAgents，失败后自动回退到 mock；同时让 `TradingAgentsGraphRunner` 按 `TRADINGAGENTS_ASTOCK_PATH` 引导导入路径。

为什么这么做：此前默认链路虽然已有真实行情和真实新闻，但深度分析仍固定使用 mock，无法自然走向真实多 Agent 投研。

收益：默认 runtime 和桌面托管 API 开始具备“真实优先、失败回退”的安全深度分析语义，后续只需继续提高真实引擎成功率和可观测性，而不是再做一次默认模式切换。

关键文件：

- `services/api/money_api/domains/analysis/tradingagents_engine.py`
- `services/api/money_api/integrations/tradingagents_runner.py`
- `services/api/money_api/api/v1/router.py`
- `apps/desktop/src/main.js`

已验证事项：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -q` 结果 `133 passed, 3 skipped`。

未做事项：`auto` 模式目前只暴露 fallback 诊断，不含更细粒度的真实 runner 配置校验、启动前检查和前端提示。

### 阶段 5.18：runtime 市场快讯接入

做了什么：新增 `ClsMarketFlashProvider` 和 `CompositeNewsProvider`，让 runtime service 在 tencent 模式下把东方财富个股新闻与 CLS 市场快讯合并写入 `DataContext.news`。

为什么这么做：阶段 5.16 只接入了个股新闻，仍缺少市场层的突发事件与宏观情绪输入，真实 TradingAgents 的上下文不完整。

收益：默认 runtime 的新闻上下文从“单股票资讯”扩展到“个股 + 市场”双层输入，后续接公告或做主题归因时不需要先重构现有 schema。

关键文件：

- `services/api/money_api/domains/market_data/cls_market_flash.py`
- `services/api/money_api/domains/market_data/eastmoney_news.py`
- `services/api/money_api/api/v1/router.py`

已验证事项：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -q` 结果 `137 passed, 3 skipped`。

未做事项：当前 market flash 只接 CLS，尚未合并东财 7x24 或交易所公告流，也未做相关性过滤。

### 阶段 5.19：runtime 公司公告标题流接入

做了什么：新增 `SinaBulletinProvider`，让 runtime service 在现有 `news` 流中继续并入公司公告标题，不扩展 `DataContext` schema。

为什么这么做：阶段 5.18 已有个股新闻和市场快讯，但仍缺少正式公告入口，真实 TradingAgents 对公司事件面的输入不完整。

收益：默认 runtime 的 `news` 上下文现在可同时覆盖个股新闻、市场快讯和公司公告标题，后续做事件分类、公告正文抓取或结构化公告时不需要先改现有契约。

关键文件：

- `services/api/money_api/domains/market_data/sina_bulletin.py`
- `services/api/money_api/api/v1/router.py`
- `services/api/tests/test_sina_bulletin.py`

已验证事项：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -q` 结果 `140 passed, 3 skipped`。

未做事项：当前只接入公告标题流，不含正文提取、交易所原文直连和事件结构化标签。

### 阶段 5.20：结构化事件流与引擎可见性

做了什么：新增 `MarketEvent` 契约、关键词事件分类器、`DataContext.events`、报告 provenance 字段（`data_sources` / `engine_source` / `engine_mode` / `fallback_reason`），并把这些信息展示到 Web 工作台和诊断面板。

为什么这么做：阶段 5.19 已经把真实资讯/公告输入面铺到标题级，但标题本身不够结构化，用户也看不出分析到底来自哪个引擎或是否发生了回退。

收益：默认 runtime 现在至少有一个可解释的结构化事件切片，用户也能直接看到本次建议的数据来源和引擎来源，降低“看起来像真分析其实已回退”的误解。

关键文件：

- `services/api/money_api/domains/analysis/contracts.py`
- `services/api/money_api/domains/analysis/market_events.py`
- `services/api/money_api/domains/analysis/service.py`
- `apps/web/src/app.js`
- `apps/web/src/mockData.js`

未做事项：事件覆盖面仍然较薄，只做了标题/摘要级的关键词分类，没有完整事件正文抽取、事件优先级体系或更细的多源归因。

已验证事项：`PYTHONPATH=services/api .venv/bin/python -m pytest services/api/tests -q` 结果 `143 passed, 3 skipped`；`python -m compileall -q services/api/money_api`；`node --check apps/web/src/app.js && node --check apps/desktop/src/main.js && node --check apps/desktop/src/preload.js`。

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
- `services/api/tests/test_sina_kline_smoke.py`
- `services/api/money_api/domains/analysis/service.py`
- `services/api/money_api/api/http.py`

已验证事项：Sina K 线真实网络 smoke 可通过 `MNS_RUN_NETWORK_SMOKE=1` 显式运行，最近结果 `1 passed`。

未做事项：复权、交易成本、滑点、缓存、多 provider fallback。

### 阶段 7.3：组合风险预算

做了什么：新增组合风险预算契约和预算器，并通过 Python API 与 HTTP API 暴露。

为什么这么做：阶段 7 的风控计划仍是单股层面，组合预算让多份报告可以被统一约束总仓位和单票集中度。

收益：系统可以输出组合总仓位、现金保留、单票预算和组合规则，为后续组合页、行业约束、真实持仓接入打基础。

关键文件：

- `services/api/money_api/domains/analysis/contracts.py`
- `services/api/money_api/domains/analysis/portfolio_risk.py`
- `services/api/money_api/domains/analysis/service.py`
- `services/api/money_api/api/http.py`
- `services/api/tests/test_portfolio_risk.py`

HTTP 入口：`POST /portfolio/risk-budget`，body 可传 `{ "task_ids": [...] }`；未传时使用最近报告。

未做事项：真实持仓同步、行业/主题/相关性约束、组合 UI、自动调仓。

### 阶段 7.4：回测成本、滑点和复权参数

做了什么：新增 `BacktestOptions`，回测支持 `cost_pct`、`slippage_pct` 和 `adjustment`，结果输出净收益、裸收益、成本影响和 options 回显。

为什么这么做：阶段 7.1/7.2 的回测只看裸价格涨跌，容易高估真实可交易收益。

收益：调用方可以显式模拟交易摩擦，Web/Desktop 后续也能展示“裸收益 vs 净收益”的差异。

关键文件：

- `services/api/money_api/domains/analysis/contracts.py`
- `services/api/money_api/domains/analysis/backtest.py`
- `services/api/money_api/domains/analysis/service.py`
- `services/api/money_api/api/http.py`
- `services/api/tests/test_backtest.py`

HTTP 入口：`POST /reports/{task_id}/backtest` 的 body 可传 `{ "options": { "cost_pct": 0.001, "slippage_pct": 0.002, "adjustment": "qfq" } }`。

未做事项：真实前复权/后复权价格转换、券商费率表、印花税细分、最小佣金、成交量约束。

### 阶段 6.1：桌面托管本地 API 与 runtime service

做了什么：让 `run_http_server()` 默认使用 runtime service，并让 Electron 在没有 `MNS_DESKTOP_API_URL` 时自动尝试拉起本地 Python API server。

为什么这么做：之前桌面默认只打开离线工作台，而且即使手动起 HTTP server，默认 service 仍是离线 mock-only 装配，不足以形成“可直接使用”的本地链路。

收益：桌面端在本机已有 Python 时可以默认进入真实 HTTP API 模式；runtime service 默认会走腾讯 quote + mock 深度分析，明显比纯离线 mock 更接近可用产品。

关键文件：

- `services/api/money_api/api/v1/router.py`
- `services/api/money_api/api/http.py`
- `apps/desktop/src/main.js`
- `apps/desktop/package.json`
- `services/api/tests/test_desktop_shell.py`

环境变量：

- `MNS_DESKTOP_API_URL`：显式指定外部 API URL 时，桌面不再托管本地 server。
- `MNS_DESKTOP_PYTHON_BIN`：显式指定桌面托管 server 使用的 Python。
- `MONEY_MARKET_DATA_MODE`：默认 `tencent`。
- `MONEY_DEEP_ENGINE`：默认 `auto`，可显式切到 `mock` 或 `tradingagents`。

未做事项：随应用打包 Python runtime、独立日志窗口、重试按钮、签名、公证、DMG、自动更新。

### 阶段 6.2：桌面启动诊断

做了什么：新增 desktop startup 上下文注入，renderer 可以看到当前模式、API URL、诊断列表和最近错误；Web 工作台头部和诊断面板会展示这些信息。

为什么这么做：阶段 6.1 虽然可以自动拉起本地 API，但失败时会静默回退，用户无法判断当前是否真的连上 API。

收益：用户能明确看到当前是托管 API、外部 API、桌面离线还是浏览器离线模式，并能直接从界面读取最近一次启动失败原因。

关键文件：

- `apps/desktop/src/main.js`
- `apps/desktop/src/preload.js`
- `apps/web/index.html`
- `apps/web/src/app.js`
- `services/api/tests/test_web_workbench.py`

未做事项：独立日志窗口、重试按钮、更细粒度的 Python 探测和日志持久化。

### 阶段 5.6：HTTP 任务队列与状态轮询

做了什么：新增 in-memory analysis task queue、`POST /tasks/analysis`、`GET /tasks/{id}`，并让 Web 工作台在连接 HTTP API 时优先走任务创建与轮询。

为什么这么做：同步 `POST /analysis` 对 mock 和轻量查询足够，但真实深度分析会变成长请求，前端需要稳定的排队和轮询入口。

收益：Web 和桌面在真实 API 模式下不再依赖长同步阻塞；任务完成后会自动拉最终报告，失败时仍可回退到离线 mock。

关键文件：

- `services/api/money_api/domains/analysis/task_queue.py`
- `services/api/money_api/api/http.py`
- `apps/web/index.html`
- `apps/web/src/app.js`
- `services/api/tests/test_http_api.py`

HTTP 入口：

- `POST /tasks/analysis`
- `GET /tasks/{task_id}`

未做事项：任务持久化、取消、重试、超时恢复、并发限流和任务历史查询。

### 阶段 5.7：任务持久化与恢复

做了什么：新增 JSON task repository、`GET /tasks` 和启动时的中断任务恢复逻辑；恢复时会把未完成任务标记为 `failed` 并附带原因。

为什么这么做：阶段 5.6 的内存任务队列一旦服务重启就会丢失上下文，前端无法再查到之前的任务状态。

收益：近期任务在服务重启后仍可查询，用户能知道哪些任务是上次运行中断导致失败，而不是静默消失。

关键文件：

- `services/api/money_api/domains/analysis/task_queue.py`
- `services/api/money_api/core/config.py`
- `services/api/money_api/api/http.py`
- `services/api/tests/test_task_queue.py`

配置项：`MONEY_TASKS_DIR`，默认 `data/cache/tasks`。

未做事项：真正的恢复执行、取消、重试、超时回收和并发限流。

### 阶段 5.8：任务取消与重试

做了什么：新增 `cancelled` 状态、`POST /tasks/{id}/cancel` 和 `POST /tasks/{id}/retry`，让失败或已取消任务可以基于原参数创建新任务。

为什么这么做：阶段 5.7 虽然让任务可持久化和恢复，但用户仍然无法控制任务生命周期，也无法方便地重新发起失败任务。

收益：真实深度分析链路终于有了最小控制面；服务端可以取消非终态任务，并对失败/取消任务创建重试任务。

关键文件：

- `services/api/money_api/domains/analysis/contracts.py`
- `services/api/money_api/domains/analysis/task_queue.py`
- `services/api/money_api/api/http.py`
- `services/api/tests/test_task_queue.py`

HTTP 入口：

- `POST /tasks/{task_id}/cancel`
- `POST /tasks/{task_id}/retry`

未做事项：真正的线程/外部请求中断、超时回收、自动重试、前端 cancel/retry 按钮。

### 阶段 5.9：任务超时回收

做了什么：新增 `started_at`、`timeout_s` 和读取路径上的超时检查；超时中的任务会自动转为 `failed` 并写明超时秒数。

为什么这么做：阶段 5.8 让任务可以取消和重试，但如果调用方既不取消也不重试，长时间卡住的任务仍会导致前端无限轮询。

收益：即使没有人工干预，超时任务也会自动收敛成明确失败状态，前端可据此结束轮询并展示错误。

关键文件：

- `services/api/money_api/core/config.py`
- `services/api/money_api/domains/analysis/task_queue.py`
- `services/api/money_api/api/http.py`
- `services/api/tests/test_task_queue.py`

配置项：`MONEY_TASK_TIMEOUT_S`，默认 `300`。

未做事项：真正的后台 watchdog、自动重试、前端超时配置 UI。

### 阶段 5.10：任务 watchdog 与自动重试

做了什么：新增后台 watchdog 扫描、`max_retries` 和 `retry_count`；超时或执行失败的任务在仍有剩余次数时可自动派生 retry task。

为什么这么做：阶段 5.9 的超时回收依赖读取路径，如果前端停止轮询，任务不会主动收敛；同时失败任务依然需要人工 retry。

收益：即使没有新的读请求，后台也会定期扫过超时任务；对可重试失败任务，服务端可以自动再次尝试，减少人工介入。

关键文件：

- `services/api/money_api/domains/analysis/task_queue.py`
- `services/api/money_api/api/http.py`
- `services/api/tests/test_task_queue.py`
- `services/api/tests/test_http_api.py`

未做事项：复杂退避策略、重试黑名单、前端 retry 配置、分布式 worker。

### 阶段 5.11：Web 任务控制 UI

做了什么：在 Web 工作台增加 `取消任务` 和 `重试任务` 按钮，并维护当前任务 ID、当前任务状态和最近失败任务 ID。

为什么这么做：阶段 5.8-5.10 已经有完整的服务端任务控制链路，但如果用户不能在页面上触发这些能力，实际可用性仍然不够。

收益：真实 API 模式下，用户可以直接在工作台取消当前任务或重试失败任务，前后端控制面终于闭环。

关键文件：

- `apps/web/index.html`
- `apps/web/src/app.js`
- `apps/web/src/styles.css`
- `services/api/tests/test_web_workbench.py`

未做事项：完整任务历史面板、批量控制、重试策略可视化、任务列表级操作。

### 阶段 5.12：Web 任务历史视图

做了什么：在 Web 工作台增加最近任务历史列表，并在任务创建、取消、重试后刷新列表。

为什么这么做：阶段 5.11 虽然可以控制当前任务，但用户依然看不到最近有哪些任务失败、取消或完成，任务可观察性不足。

收益：真实 API 模式下，用户可以直接看到近期任务状态和失败原因，减少“当前任务结束后信息丢失”的体验断层。

关键文件：

- `apps/web/index.html`
- `apps/web/src/app.js`
- `services/api/tests/test_web_workbench.py`

未做事项：任务详情页、筛选、分页、批量控制。

### 阶段 3 验证补充：真实 TradingAgents smoke

做了什么：执行 `MNS_RUN_TRADINGAGENTS_SMOKE=1 PYTHONPATH=services/api ...test_tradingagents_smoke.py`。

结果：`1 passed`。

意义：确认当前 Money_Never_sleep 到 TradingAgents-astock 的真实 runner 链路在本机环境下可被调起，不再只是 mock 或设计级接入。

### 阶段 5.44：真实 TradingAgents 主路径强化

做了什么：`TradingAgentsGraphRunner` 默认 analyst 扩为 `market/social/news/fundamentals/policy/hot_money/lockup`，真实运行时合并 TradingAgents-astock 默认配置和本仓库 `TRADINGAGENTS_*` 缓存路径，并把 analyst 报告、投研辩论、风险辩论和组合经理结论映射到 `AgentView`。

为什么这么做：用户决定优先完成真实 agent 分析上线。此前真实 runner 可以调起 graph，但输出映射和可观测字段太薄，无法判断这次是否真正命中了多 Agent 主路径。

收益：报告和任务历史现在可以看到真实 TradingAgents 命中/回退、provider、deep/quick 模型、角色、耗时和上下文快照；`auto` 仍能失败后回退到工具驱动分析。

关键文件：

- `services/api/money_api/integrations/tradingagents_runner.py`
- `services/api/money_api/domains/analysis/tradingagents_engine.py`
- `apps/web/src/app.js`
- `apps/web/src/mockData.js`
- `services/api/tests/test_tradingagents_runner.py`
- `services/api/tests/test_web_workbench.py`

未做事项：尚未把 Money_Never_sleep 的 provider 直接注入 TradingAgents-astock 工具层；真实 smoke 仍需要本机 LLM provider/API key 环境就绪。

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

可选 Sina K 线网络 smoke：

```bash
MNS_RUN_NETWORK_SMOKE=1 PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_sina_kline_smoke.py -v
```

可选 TradingAgents smoke：

```bash
MNS_RUN_TRADINGAGENTS_SMOKE=1 PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_tradingagents_smoke.py -v
```

阶段 5.44 定向验证：

```bash
PYTHONPATH=services/api pytest -q services/api/tests
python3 -m compileall -q services/api/money_api services/api/tests
node --check apps/web/src/app.js && node --check apps/web/src/mockData.js
```

结果：`170 passed, 3 skipped`，Python 语法检查和 Web JS 语法检查通过。

## 当前已知限制

- Web 工作台默认仍是离线 mock；真实 HTTP API 需要通过 `?api=` 显式启用。
- `apps/desktop` 已有 Electron 第一版壳、macOS `.app` 构建入口、托管本地 API server 和启动诊断；但尚未签名、公证、打 DMG、设置图标，也未随应用打包 Python runtime。
- runtime 默认深度引擎是 `auto`：优先真实 TradingAgents，失败后回退工具驱动分析；显式 `MONEY_DEEP_ENGINE=tradingagents` 用于严格真实引擎诊断。
- 数据层真实 provider 覆盖腾讯 quote 最小路径和 Sina 日线 K 线回测价格序列。
- 报告 repository 使用 JSON 文件，适合第一版，不适合复杂查询和并发写入。
- 已有第一版任务持久化、状态轮询、中断恢复标记、cancel/retry 控制、超时回收、自动重试和最小前端入口，但还没有真正的恢复执行、强制中断和复杂退避语义。
- 风控纪律、回测和组合预算已完成第一版，但尚未接真实交易执行或真实持仓同步。
- 回测接口已接入 Sina 日线 K 线 provider，并支持成本、滑点和复权标记；尚未做真实复权价格转换、缓存和多 provider fallback。
- 组合风险预算已完成第一版，但尚未接真实持仓、行业/主题/相关性约束和 Web/Desktop 组合视图。

## 推荐下一步

建议继续阶段 7 后续切片：真实复权价格转换、回测缓存、多 provider fallback，或组合预算的行业/相关性约束；如果更偏服务化和产品化，可以先补真实 TradingAgents smoke、更细粒度的重试/退避策略和任务历史 UI。

推荐第一版路径：

1. 设计产品级风险纪律和免责声明。
2. 建立可复盘的信号/建议记录。
3. 再考虑回测、组合、绩效归因。
4. 桌面端可并行补签名、公证、DMG、图标和自动更新。

如果更想继续服务化，可以从 `docs/improvement-backlog.md` 的 `MNS-BL-013` 或 `MNS-BL-014` 开始：升级 FastAPI/OpenAPI，或设计异步任务队列和状态轮询。

## 给后续 agent 的注意事项

- 不要直接复制参考项目的大块源码。
- 不要把 secrets、模型名、绝对路径或本机端口写死进代码。
- 本仓库的项目本地 skills 位于 `.github/superpowers/`；阶段、backlog 或第二版功能切片优先使用 `.github/superpowers/mns-stage-delivery/SKILL.md`。
- 如果重复工作暴露出可复用 workflow 或技巧，不要只留在聊天里；项目特定内容沉淀到 `.github/superpowers/`，规则性约束写入 `.github/copilot-instructions.md` 或对应 docs。
- 完成任何阶段时，必须更新 `README.md`、`docs/stages.md`、`docs/improvement-backlog.md` 和本文件中相关部分。
- 如果新增信息入口、文档职责或写回规则，必须更新 `docs/information-map.md`。
- 如果第一版推迟了某个功能，必须把原因和下一步写入 `docs/improvement-backlog.md`。
- 如果新增验证命令或构建入口，必须写到本文件和对应阶段文档。
