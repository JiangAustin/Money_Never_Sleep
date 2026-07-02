# 决策日志

状态：活文档
最近更新：2026-07-03

这个文件记录每一次工作切片的短记忆，目标是防止对话压缩后丢失“做了什么、为什么做、验证到什么程度、下一步是什么”。内容尽量短，保留可检索性。

## 2026-07-02 Web 研究工具调试面板

- 做了什么：在 Web 工作台的诊断区新增“研究工具调试”面板，自动按当前报告股票拉取 `context / quote / technicals / fundamentals / news / capital-flow / longhubang / unlocks` 的返回值，并用可展开的原始 JSON 形式展示。
- 为什么：研究工具 API 已经有了，但如果前端看不到真实返回值，就很难快速验证东财、同花顺和行情 provider 的结果是否正确，也不利于排查回退和数据缺口。
- 验证：`python3 -m compileall -q services/api/money_api services/api/tests`；`node --check apps/web/src/app.js`；`PYTHONPATH=services/api pytest -q services/api/tests/test_web_workbench.py services/api/tests/test_research_tools.py` 结果 `12 passed`。
- 下一步：继续把公告正文、资金流和更细的事件层接进可视化和工具目录，别把 Web 面板做成第二个孤立数据源。

## 2026-07-02 公告正文薄切片

- 做了什么：把 `SinaBulletinProvider` 从标题流升级为标题+正文薄切片，新增公告详情页正文抓取与清洗逻辑，并让 `DataContext` 的结构化事件抽取可以直接消费公告正文。
- 为什么：仅有公告标题还不够，A 股里很多高价值信号出现在正文里；先把公告正文接上，能最小代价提升事件命中质量，而不必先新做一个数据家族。
- 验证：`python3 -m compileall -q services/api/money_api services/api/tests`；`node --check apps/web/src/app.js`；`PYTHONPATH=services/api pytest -q services/api/tests/test_sina_bulletin.py services/api/tests/test_analysis_api.py services/api/tests/test_web_workbench.py` 结果 `27 passed`。
- 下一步：继续补资金流和龙虎榜，但保持同一条 `news`/`events` 管线，不要再分裂成平行数据源。

## 2026-07-02 资金流调试摘要

- 做了什么：把 Web 研究工具调试面板里的 `capital_flow / longhubang / unlocks` 结果从纯原始 JSON 升级成带摘要的可读展示，直接显示主力净流入、龙虎榜净额、解禁数量等核心字段。
- 为什么：资金流、龙虎榜和解禁已经接成工具入口，但如果页面只给 JSON，不利于快速判断数据是否有价值，也不方便直接给 agent 或用户扫读。
- 验证：`python3 -m compileall -q services/api/money_api services/api/tests`；`node --check apps/web/src/app.js`；`PYTHONPATH=services/api pytest -q services/api/tests/test_web_workbench.py services/api/tests/test_sina_bulletin.py` 结果 `12 passed`。
- 下一步：继续把这些摘要和报告详情的投资计划/风险语境对齐，再决定要不要把更深的数据面升成独立的业务视图。

## 2026-07-02 龙虎榜方向摘要

- 做了什么：把 Web 研究工具调试面板里的 `longhubang` 摘要再细化，除了净额、买额、卖额和机构买额，还会明确标出净流入、净流出或持平。
- 为什么：龙虎榜净额本身还不够直观，直接显示方向更利于快速判断信号强弱，也更接近实盘浏览时的扫读方式。
- 验证：`python3 -m compileall -q services/api/money_api services/api/tests`；`node --check apps/web/src/app.js`；`PYTHONPATH=services/api pytest -q services/api/tests/test_web_workbench.py services/api/tests/test_sina_bulletin.py services/api/tests/test_analysis_api.py` 结果 `27 passed`。
- 下一步：如果后面继续往深做，可以把龙虎榜方向和报告里的风险控制/投资计划做更强的关联，但不要把调试面板做成另一个独立分析页。

## 2026-07-02 研究信号联动摘要

- 做了什么：在 Web 报告详情页新增“研究信号”摘要区，把资金流、龙虎榜、公告线索和结构化事件压成一段与投资计划相邻的可读判读。
- 为什么：调试面板解决了“看得到原始数据”，但用户还需要一眼看出这些数据对当前投资计划和风控的方向意味着什么。
- 验证：`python3 -m compileall -q services/api/money_api services/api/tests`；`node --check apps/web/src/app.js`；`PYTHONPATH=services/api pytest -q services/api/tests/test_web_workbench.py services/api/tests/test_sina_bulletin.py services/api/tests/test_analysis_api.py` 结果 `27 passed`。
- 下一步：如果继续做联动，可以把研究信号和 `InvestmentPlan` 的理由文本进一步对齐，但不要引入新的独立分析层。

## 2026-07-02 研究信号与计划对齐

- 做了什么：把 Web 报告详情页里的“研究信号”摘要进一步和 `InvestmentPlan` 对齐，直接显示计划方向、目标仓位、止损/止盈，并给出“计划与研究信号一致/分歧”的判读。
- 为什么：用户需要看到的不只是研究数据，还要看到这些信号为什么支撑当前计划，或者为什么需要更保守。
- 验证：`python3 -m compileall -q services/api/money_api services/api/tests`；`node --check apps/web/src/app.js`；`PYTHONPATH=services/api pytest -q services/api/tests/test_web_workbench.py services/api/tests/test_sina_bulletin.py services/api/tests/test_analysis_api.py` 结果 `27 passed`。
- 下一步：如果继续增强联动，可以把这段判读再回写到后端计划理由，但前提是能证明比当前前端对齐更有价值。

## 2026-07-03 投资计划证据范围回写

- 做了什么：把 `InvestmentPlan` 的理由和风险说明继续回写为证据可见文本，新增对高优先级事件证据范围的解释，让计划层能说明这次建议更依赖标题、正文还是两者都命中。
- 为什么：研究信号摘要已经能告诉用户“发生了什么”，但计划层还需要说明“这次建议主要基于什么证据、证据来自哪里、有没有回退到更弱的线索”，否则 `auto` 或结构化事件仍容易被误读成黑箱结论。
- 验证：`python3 -m compileall -q services/api/money_api services/api/tests`；`PYTHONPATH=services/api pytest -q services/api/tests/test_analysis_service.py services/api/tests/test_analysis_api.py services/api/tests/test_web_workbench.py` 结果 `29 passed`。
- 下一步：继续把证据范围回写到更多计划解释位，但保持最小闭环，不再新增并列计划模型。

## 2026-07-03 投资计划正负证据拆线

- 做了什么：把 `InvestmentPlan` 的解释进一步拆成正向证据和风险证据两条线，正向信号和风险信号现在可以分别说明自己主要来自标题、正文还是两者都命中。
- 为什么：总证据范围能减少黑箱感，但对于基金经理式计划来说，还需要明确“做多的依据”和“防守的依据”各自来自哪里，才能让 rationale / risk_notes 更像可执行的研究笔记。
- 验证：`python3 -m compileall -q services/api/money_api services/api/tests`；`PYTHONPATH=services/api pytest -q services/api/tests/test_analysis_service.py services/api/tests/test_analysis_api.py`。
- 下一步：如果继续补计划解释位，优先把这条拆线复用到更复杂的事件组合，不要再堆第三种同义总结。

## 2026-07-03 投资计划证据展示

- 做了什么：在 Web 报告详情页的“投资计划”区块新增了轻量“证据来源”小节，直接展示正向证据和风险证据的来源摘要；离线 mock 也同步补齐同名字段。
- 为什么：后端已经把计划解释拆到正负证据两条线，但如果 Web 只显示理由和风险备注，用户还是得在研究信号里猜来源；把证据来源贴回计划区块更符合基金经理式阅读路径。
- 验证：`node --check apps/web/src/app.js`。
- 下一步：如果再扩展这个展示，只在计划区块里做轻量补充，不另起新面板。

## 2026-07-03 报告列表证据摘要

- 做了什么：把 `InvestmentPlan` 的正向/风险证据摘要同步到报告列表卡片，让列表页也能直接扫到当前报告的证据方向。
- 为什么：列表页是进入报告的第一眼，如果这里只显示标题和总摘要，用户还要点进去才知道这份计划是偏多还是偏防守；把证据摘要放进列表能减少上下文切换。
- 验证：`node --check apps/web/src/app.js`；`node --check apps/web/src/mockData.js`。
- 下一步：如果还要继续压缩列表信息，只保留一行证据摘要，不再增加第二层卡片结构。

## 2026-07-02 结构化事件流与引擎可见性

- 做了什么：新增 `MarketEvent` 契约、结构化事件分类器、`DataContext.events`、报告 provenance 字段（`data_sources` / `engine_source` / `engine_mode` / `fallback_reason`），并把这些信息展示到 Web 工作台和诊断区。
- 为什么：默认 runtime 已经有真实行情、新闻和公告标题，但还缺少“可解释的事件切片”和“这次分析到底来自哪个引擎”的可见性。
- 验证：`PYTHONPATH=services/api .venv/bin/python -m pytest services/api/tests -q` 结果 `143 passed, 3 skipped`；`python -m compileall -q services/api/money_api`；`node --check apps/web/src/app.js && node --check apps/desktop/src/main.js && node --check apps/desktop/src/preload.js`。
- 下一步：继续扩展结构化事件的覆盖面，补事件正文/更细分类/优先级体系，再把事件直接串进更专业的投资计划模板。

## 2026-07-02 Agent 研究工具入口

- 做了什么：把现有在线 market data bundle 再包装成 `ResearchToolService`，并通过 HTTP/Python 暴露 `context`、`quote`、`technicals`、`fundamentals` 和 `news` 五类研究工具入口。
- 为什么：仅有整份分析报告还不够，外部 agent 和上层工作流需要更细粒度的工具目录，才能直接调用东财、同花顺和行情 provider，而不是先绕一圈报告生成。
- 验证：`python3 -m compileall -q services/api/money_api services/api/tests`；`env PYTHONPATH=services/api ...python3 -c` smoke，覆盖研究工具上下文、fundamentals provider 链和 HTTP `/research/context`。
- 下一步：继续把资金流、龙虎榜、解禁和公告正文补进在线工具层，然后再考虑是否需要 MCP 风格的更完整工具编排。

## 2026-07-02 研究工具薄切片扩展

- 做了什么：在 `ResearchToolService` 上继续补齐资金流、龙虎榜和解禁三类独立工具入口，并把它们通过 HTTP/Python 一起暴露出来。
- 为什么：用户明确希望先把“尽快可用”的工具入口补全，A 股研究助手除了基本面和行情，还需要能直接查到主力资金、龙虎榜和解禁压力。
- 验证：`python3 -m compileall -q services/api/money_api services/api/tests`；`env PYTHONPATH=services/api ...python3 -c` smoke，覆盖 `capital_flow`、`longhubang`、`unlocks` 和 HTTP `/research/unlocks`。
- 下一步：继续把公告正文补进工具层，再考虑是否需要把这些工具做成更完整的 agent 编排层。

## 2026-07-02 在线工具数据层与工具驱动回退

- 做了什么：把 runtime 数据层从静态 fallback 升级成在线工具层，新增东财 F10 fundamentals provider、Sina K 线技术指标 provider、可选同花顺问财 fundamentals provider 和 runtime provider bundle；同时把 `auto` 回退从纯 mock 改成工具驱动报告。
- 为什么：用户明确要求“尽快可以用”，不能再让默认 runtime 看起来像离线 demo。真实行情、技术指标、基本面和资讯必须直接从在线工具层进入报告。
- 验证：`python3 -m compileall -q services/api/money_api services/api/tests`；`env PYTHONPATH=services/api ...python3 -c` 两个 smoke，分别覆盖 `build_runtime_analysis_service(..., FakeTradingAgentsRunner())` 和 `auto` 失败回退到 `tool-driven` 报告。
- 下一步：继续补资金流、龙虎榜、解禁和公告正文，然后再把工具层包装成更完整的 agent 可调用目录。

## 2026-07-02 全局架构入口文档

- 做了什么：在仓库根目录新增 `ARCHITECTURE.md`，把核心模块划分、数据流向、设计原则和参考项目政策写成后续任务入口；同时在 `README.md` 和 `docs/information-map.md` 中把它标为新任务第一阅读入口。
- 为什么：项目周期较长，后续记忆会压缩，需要一个比 README 更直接的全局规范入口，减少新任务时反复解释背景。
- 验证：文件已创建并在 `README.md`、`docs/information-map.md` 中建立跳转；本次变更无代码路径变更，未额外跑测试。
- 下一步：后续所有新任务默认先读 `ARCHITECTURE.md`，再读阶段文档和对应模块。

## 2026-07-02 review 补强与长期规则

- 做了什么：采纳 review 的必须修改和建议修改，完成未知事件类型安全降级、单条资讯多事件输出、旧 JSON 报告 provenance 回填；新增 `docs/reference-integration-map.md`；把参考项目长期使用规则和模型使用规则写入 `AGENTS.md`。
- 为什么：避免事件契约和报告历史在后续扩展时脆弱，同时防止长周期项目在对话压缩后丢失三个参考项目的可复用资产判断。
- 验证：目标测试 `PYTHONPATH=services/api .venv/bin/python -m pytest services/api/tests/test_analysis_contracts.py services/api/tests/test_market_events.py services/api/tests/test_report_repository.py -q` 结果 `25 passed`。
- 下一步：跑完整后端测试和前端语法检查；下一阶段设计 `InvestmentPlan`、`DataTrustScore` 和模型/引擎成本治理。

## 2026-07-02 投资计划契约第一版

- 做了什么：新增 `InvestmentPlan` 契约，把它挂到 `AnalysisReport` 上，并由 `AnalysisService` 基于最终报告和风控结果自动生成；Web 离线 mock 和详情页也补出了同名字段和展示区块。
- 为什么：当前报告已有 action 和 risk plan，但还缺少更像基金经理工作流的“执行计划”层，无法直接给出入场、退出、复核和观察窗口。
- 验证：`PYTHONPATH=services/api .venv/bin/python -m pytest services/api/tests/test_analysis_contracts.py services/api/tests/test_analysis_service.py services/api/tests/test_analysis_api.py services/api/tests/test_http_api.py services/api/tests/test_web_workbench.py -q` 结果 `64 passed`；`python -m compileall -q services/api/money_api`；`node --check apps/web/src/app.js`。
- 下一步：在不扩散范围的前提下继续做 `DataTrustScore` 和模型/引擎成本治理，保持计划、风控和可见性三层分离。

## 2026-07-02 数据可信度评分第一版

- 做了什么：新增 `DataTrustScore` 契约，把它挂到 `AnalysisReport` 上，并由 `AnalysisService` 基于 `data_sources`、`gaps`、`diagnostics` 和回退信息自动生成；Web 离线 mock 和详情页也补出了同名字段和展示区块。
- 为什么：用户需要一眼看出建议依赖的数据到底有多可靠，不能只看 action 和风险，还要知道真实来源、缺口和回退是否存在。
- 验证：`PYTHONPATH=services/api .venv/bin/python -m pytest services/api/tests/test_analysis_contracts.py services/api/tests/test_analysis_service.py services/api/tests/test_analysis_api.py services/api/tests/test_http_api.py services/api/tests/test_web_workbench.py -q` 结果 `65 passed`；`python -m compileall -q services/api/money_api`；`node --check apps/web/src/app.js`。
- 下一步：只剩模型/引擎成本治理，避免继续堆计划层字段。

## 2026-07-02 引擎运行画像第一版

- 做了什么：新增 `EngineTelemetry` 契约，把它挂到 `AnalysisReport` 上，并由 `AnalysisService` 记录运行时长、执行路径、请求次数、成本层级和失败信息；Web 离线 mock 和详情页也补出了同名字段和展示区块。
- 为什么：`DataTrustScore` 解决了“数据有多可靠”，但还要让用户看见“引擎到底走了哪条路、花了多少代价、有没有失败回退”。
- 验证：`PYTHONPATH=services/api .venv/bin/python -m pytest services/api/tests/test_analysis_contracts.py services/api/tests/test_analysis_service.py services/api/tests/test_analysis_api.py services/api/tests/test_http_api.py services/api/tests/test_web_workbench.py -q` 结果 `66 passed`；`python -m compileall -q services/api/money_api`；`node --check apps/web/src/app.js`。
- 下一步：只剩模型/引擎成本阈值和告警治理，不再继续堆计划层字段。

## 2026-07-02 引擎成本治理第一版

- 做了什么：新增 `EngineCostGuardrail` 契约，把它挂到 `AnalysisReport` 上，并由 `AnalysisService` 基于 `EngineTelemetry` 自动生成成本阈值、告警和预算命中情况；Web 离线 mock 和详情页也补出了同名字段和展示区块。
- 为什么：`EngineTelemetry` 解决了“引擎花了什么代价”，但还需要把这次代价是否超出预设预算说清楚，避免长期使用时把成本风险留在口头判断里。
- 验证：`PYTHONPATH=services/api .venv/bin/python -m pytest services/api/tests/test_analysis_contracts.py services/api/tests/test_analysis_service.py services/api/tests/test_analysis_api.py services/api/tests/test_http_api.py services/api/tests/test_web_workbench.py -q` 结果 `67 passed`；`python -m compileall -q services/api/money_api`；`node --check apps/web/src/app.js`。
- 下一步：如果后续还要做计划层扩展，必须先证明它解决的是新的真实问题，而不是继续堆字段。

## 2026-07-02 结构化事件覆盖扩展第一版

- 做了什么：在现有结构化事件第一切片上继续扩展 `MarketEventType` 和分类规则，新增股份回购与股权质押两类高价值事件，并把离线 Web mock 也同步补齐。
- 为什么：已有事件切片能覆盖基本面和部分风险信号，但还缺少对股东回报和股权风险这两类常见 A 股事件的直接表达。
- 验证：`PYTHONPATH=services/api .venv/bin/python -m pytest services/api/tests/test_market_events.py services/api/tests/test_analysis_service.py services/api/tests/test_analysis_contracts.py services/api/tests/test_web_workbench.py -q` 结果 `35 passed`；`python -m compileall -q services/api/money_api`；`node --check apps/web/src/app.js && node --check apps/web/src/mockData.js`。
- 下一步：继续扩事件正文、优先级和更多高价值类别，再把事件层更紧地串进投资计划模板。

## 2026-07-02 结构化事件优先级第一版

- 做了什么：给 `MarketEvent` 新增 `priority` 字段，并为业绩预告、减持、担保、解禁、回购和股权质押等事件映射出优先级；Web 事件卡片也同步展示这一层信息。
- 为什么：仅有事件类型还不够，后续投资计划和排序逻辑需要知道哪些信号更应先看、先解释、先处理。
- 验证：`PYTHONPATH=services/api .venv/bin/python -m pytest services/api/tests/test_market_events.py services/api/tests/test_analysis_contracts.py services/api/tests/test_analysis_service.py services/api/tests/test_analysis_api.py services/api/tests/test_web_workbench.py -q` 结果 `49 passed`；`python -m compileall -q services/api/money_api`；`node --check apps/web/src/app.js && node --check apps/web/src/mockData.js`。
- 下一步：把优先级直接串到投资计划生成里，让高优先级事件对建议方向和仓位产生更明确的影响。

## 2026-07-02 事件优先级驱动计划第一版

- 做了什么：`AnalysisService` 现在会汇总高优先级正负事件，并在深度分析时据此调整 `InvestmentPlan` 的方向和仓位；轻量查询仍保持原样。
- 为什么：事件层只有标签还不够，必须能真正改变建议方向，才算进入了可用的投研链路。
- 验证：`PYTHONPATH=services/api .venv/bin/python -m pytest services/api/tests/test_analysis_service.py services/api/tests/test_analysis_api.py services/api/tests/test_http_api.py services/api/tests/test_market_events.py services/api/tests/test_analysis_contracts.py services/api/tests/test_web_workbench.py -q` 结果 `72 passed`；`python -m compileall -q services/api/money_api`；`node --check apps/web/src/app.js && node --check apps/web/src/mockData.js`。
- 下一步：继续把事件信号细化到正文和更多高价值类别，再考虑是否需要独立的事件排序/评分模块。

## 2026-07-02 结构化事件证据范围第一版

- 做了什么：给 `MarketEvent` 新增 `evidence_scope`，并让事件抽取器标注命中来自标题、正文还是两者都命中；Web 离线样例和事件卡片也同步展示。
- 为什么：仅知道事件类型和优先级还不够，正文级别命中和标题级别命中的解释力度不同，需要显式分开。
- 验证：`PYTHONPATH=services/api .venv/bin/python -m pytest services/api/tests/test_market_events.py services/api/tests/test_analysis_contracts.py services/api/tests/test_analysis_service.py services/api/tests/test_analysis_api.py services/api/tests/test_http_api.py services/api/tests/test_web_workbench.py -q` 结果 `74 passed`；`python -m compileall -q services/api/money_api`；`node --check apps/web/src/app.js && node --check apps/web/src/mockData.js`。
- 下一步：继续把正文级别事件扩成更多高价值类别，再考虑是否需要独立的事件排序/评分模块。

## 2026-07-02 结构化事件证据片段第一版

- 做了什么：给 `MarketEvent` 新增 `evidence_excerpt`，并让抽取器根据标题或正文命中截取原文片段；Web 离线样例和事件卡片也同步展示。
- 为什么：只有证据范围还不够，用户需要直接看到命中的原文片段，才能快速判断抽取结果是否合理。
- 验证：`PYTHONPATH=services/api .venv/bin/python -m pytest services/api/tests/test_market_events.py services/api/tests/test_analysis_contracts.py services/api/tests/test_analysis_service.py services/api/tests/test_analysis_api.py services/api/tests/test_http_api.py services/api/tests/test_web_workbench.py -q` 结果 `74 passed`；`python -m compileall -q services/api/money_api`；`node --check apps/web/src/app.js && node --check apps/web/src/mockData.js`。
- 下一步：继续把正文级别事件扩成更多高价值类别，再考虑是否需要独立的事件排序/评分模块。

## 2026-07-02 结构化事件正文可读性第一版

- 做了什么：继续沿着 `evidence_excerpt` 完善前端展示，让正文命中的片段在事件卡片里直接可读。
- 为什么：解释性字段必须服务于“肉眼可扫读”，否则只是把契约做厚，没有真正改善投研阅读。
- 验证：`PYTHONPATH=services/api .venv/bin/python -m pytest services/api/tests/test_market_events.py services/api/tests/test_analysis_contracts.py services/api/tests/test_analysis_service.py services/api/tests/test_analysis_api.py services/api/tests/test_http_api.py services/api/tests/test_web_workbench.py -q` 结果 `74 passed`；`python -m compileall -q services/api/money_api`；`node --check apps/web/src/app.js && node --check apps/web/src/mockData.js`。
- 下一步：继续把正文级别事件扩成更多高价值类别，再考虑是否需要独立的事件排序/评分模块。

## 2026-07-02 结构化事件增持信号第一版

- 做了什么：新增 `MarketEventType.SHARE_INCREASE`，把股东增持作为高优先级正向事件接进事件规则、计划推导和 Web mock。
- 为什么：增持是 A 股里很常见且对方向判断有用的正向信号，适合继续验证“事件层可以改变投资计划”这条链路。
- 验证：`PYTHONPATH=services/api .venv/bin/python -m pytest services/api/tests/test_market_events.py services/api/tests/test_analysis_service.py services/api/tests/test_analysis_api.py services/api/tests/test_http_api.py services/api/tests/test_analysis_contracts.py services/api/tests/test_web_workbench.py -q` 结果 `76 passed`；`python -m compileall -q services/api/money_api`；`node --check apps/web/src/app.js && node --check apps/web/src/mockData.js`。
- 下一步：继续扩正文级高价值类别，再考虑是否需要独立的事件排序/评分模块。
