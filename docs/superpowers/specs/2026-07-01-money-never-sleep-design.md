# Money_Never_sleep 设计规格

日期：2026-07-01  
状态：待用户审查  
阶段：Brainstorming 设计规格，不包含实现计划和代码改动

## 1. 背景与目标

Money_Never_sleep 的目标不是做一个简单的股票问答工具，而是构建一个长期可演进的 A 股智能投研平台。平台需要帮助用户进行股票分析、投资理财决策辅助、风险识别和复盘，但必须保持可解释、可追溯、可验证，不能以黑箱荐股或承诺收益作为产品核心。

第一阶段成功标准选择为“长期平台优先”：先建立清晰的平台边界和核心契约，再接入深度 AI 分析能力。这样可以避免直接 fork 任一参考项目后被既有结构锁死，也避免从零开始重复造已有能力。

## 2. 参考项目结论

### 2.1 TradingAgents-astock

定位：A 股深度多 Agent 投研引擎。

优点：

- 具备最强的 AI 投研链路：市场、舆情、新闻、基本面、政策、游资、解禁等 7 类分析师。
- 具备 Bull/Bear 辩论、Research Manager、Trader、风险辩论和 Portfolio Manager 的完整推理结构。
- A 股特化程度高，覆盖政策市、游资、解禁、T+1、涨跌停等本地市场特征。
- 数据层大量使用免费直连源，适合个人或本地使用场景。

不足：

- 更像投研引擎，不是完整产品平台。
- API、任务调度、历史报告、用户配置、组合管理、权限、桌面客户端等产品层能力较薄。
- 全量多 Agent 分析成本较高，不适合所有轻量问题都调用完整流程。
- 直接作为项目基座会迫使 Money_Never_sleep 后续补大量平台能力。

采纳方式：作为 Money_Never_sleep 的深度 AI 投研引擎参考和优先集成对象，而不是作为整体产品基座。

### 2.2 daily_stock_analysis

定位：成熟的股票分析产品工程骨架。

优点：

- API、Web、桌面、报告、通知、历史记录、配置管理、任务状态等产品面完整。
- 数据源管理、fallback、市场代码标准化、缓存和诊断机制更成熟。
- 测试数量和 CI 覆盖较完整，适合作为工程质量参考。
- 已经有 Agent API、多 Agent 产品化编排、策略技能、报告输出等可借鉴模块。

不足：

- 功能面很大，直接 fork 容易继承历史复杂度和非目标功能。
- Agent 体系偏产品内问股和仪表盘分析，深度投研结构不如 TradingAgents-astock 集中。
- 若作为基座，Money_Never_sleep 容易变成 daily_stock_analysis 的变体，而不是独立平台。

采纳方式：吸收服务化边界、数据 fallback、任务、报告、通知、Web/API 工程模式，不整体复制。

### 2.3 go-stock

定位：本地桌面股票分析工具和丰富工具箱。

优点：

- Wails + Vue + NaiveUI 的桌面体验较成熟。
- 行情、K 线、自选股分组、提醒、图表、市场资讯、AI 助手等本地交互丰富。
- Agent 具备 ReAct 和 PlanExecute 两种模式，并通过工具分组按问题选择工具。
- MCP 工具、提示词模板、行情组件和本地应用打包经验值得参考。

不足：

- Go/Wails 技术栈与 Money_Never_sleep 当前 Python AI 服务生态存在集成成本。
- 更偏桌面工具软件，不适合作为 AI 投研平台核心后端。
- GPLv3 许可证会限制直接复制和混合代码的方式。

采纳方式：借鉴桌面体验、图表交互、工具分组、MCP 和本地打包思路，不作为核心基座。

## 3. 推荐路线

推荐路线：Money_Never_sleep 自建平台骨架，TradingAgents-astock 作为深度 AI 投研引擎，daily_stock_analysis 提供工程模式参考，go-stock 提供桌面和工具体验参考。

原因：

- 长期平台优先需要 Money_Never_sleep 自己控制领域模型、API 合约、插件边界和演进节奏。
- TradingAgents-astock 的 AI 投研结构价值最高，但产品外壳不足，适合作为引擎层而不是全项目基座。
- daily_stock_analysis 的工程能力很强，但直接 fork 会带来复杂历史包袱。
- go-stock 的桌面体验优秀，但不适合承担 Python AI 平台的核心服务层。

## 4. 产品边界

### 4.1 第一阶段范围

第一阶段聚焦“单股深度分析闭环”：

1. 用户输入 A 股代码或股票名称。
2. 系统解析并标准化股票标识。
3. 数据层聚合行情、K 线、财务、新闻、公告、资金流、龙虎榜、解禁等信息。
4. 快速 Agent 判断问题类型和是否需要深度分析。
5. 深度 AI 投研引擎执行多 Agent 分析。
6. 风控模块检查追高、趋势、仓位、止损、事件风险和数据缺口。
7. 输出结构化报告，包括结论、理由、风险、关键证据、置信度和后续观察点。
8. 保存历史报告，支持复盘和追问。

### 4.2 第一阶段不做

- 不承诺自动赚钱或收益率。
- 不做全自动实盘交易。
- 不一开始同时完成 Web、桌面、移动端、通知、回测、选股全功能。
- 不直接复制三个参考项目的大块源码。
- 不让每个轻量查询都触发完整多 Agent 深度流程。

## 5. 总体架构

Money_Never_sleep 采用分层平台架构：

```text
apps/web、apps/desktop
        |
services/api
        |
services/analysis  ---- services/agent
        |                    |
services/data        agent engines / skills / tools
        |
data/cache、data/raw、data/processed
```

### 5.1 体验层

职责：承载用户工作流。

初期优先 Web 工作台，桌面端保持壳或延后。Web 工作台至少需要支持：输入股票、查看分析进度、阅读报告、查看历史、继续追问。

桌面端后续再比较 Wails、Electron、Tauri。go-stock 证明 Wails 可行，但 Money_Never_sleep 当前以 Python API 和 Web 前端为主，第一阶段不强制绑定 Wails。

### 5.2 平台 API 层

职责：提供稳定的服务入口和产品契约。

核心 API：

- 健康检查。
- 股票解析和基础信息。
- 创建分析任务。
- 查询任务状态。
- 获取分析报告。
- 获取历史报告。
- Agent 追问。

API 层不直接写死单一具体 AI 框架，而是调用 analysis service 和 agent engine adapter。

### 5.3 分析编排层

职责：控制一次分析任务的生命周期。

分析任务状态：

- queued：已提交。
- collecting_data：采集数据。
- quick_screening：快速判断。
- deep_analysis：深度投研。
- risk_review：风控审查。
- report_ready：报告完成。
- failed：失败。

编排层要记录每个阶段的输入摘要、输出摘要、耗时、错误和数据源情况，保证报告可追溯。

### 5.4 AI / Agent 层

职责：把不同分析深度和不同 Agent 技术路线隔离起来。

建议分为两种引擎：

1. Quick Agent：用于轻量问答、行情解释、报告追问、工具查询。
2. Deep Research Engine：用于单股深度投研，参考 TradingAgents-astock 的多 Agent 图。

Deep Research Engine 的阶段：

- Market Analyst：技术面和量价。
- Fundamentals Analyst：财务和估值。
- News Analyst：新闻、公告和事件。
- Policy Analyst：政策和行业监管。
- Hot Money Analyst：资金流、龙虎榜、游资、北向资金。
- Lockup Analyst：解禁、减持、股权压力。
- Bull/Bear Debate：多空辩论。
- Risk Debate：激进、中性、保守三方风控。
- Portfolio Decision：形成操作建议、仓位建议、观察点和风险提示。

第一阶段可以先实现适配器接口，不要求完整复刻所有节点。适配器必须隐藏底层实现，使未来可以替换为 TradingAgents-astock、LiteLLM 原生工具调用、Eino 风格 PlanExecute 或自研图执行器。

### 5.5 数据与知识层

职责：统一数据源、缓存和上下文包。

数据能力优先级：

1. 股票代码和名称解析。
2. 日线、实时行情、技术指标。
3. 财务摘要和估值。
4. 新闻、公告、研报和事件。
5. 资金流、龙虎榜、板块和解禁。
6. 分析历史、用户备注、Agent 记忆。

数据层必须输出标准结构，Agent 不直接依赖具体数据源。参考 daily_stock_analysis 的 DataFetcherManager 和 TradingAgents-astock 的 A 股直连数据源，形成 Money_Never_sleep 自己的 provider adapter。

### 5.6 风控与验证层

职责：防止系统输出无约束的投资建议。

第一阶段风控基线：

- 不追高：股价显著偏离短期均线时降低买入建议。
- 趋势确认：多头排列和量价关系必须进入理由。
- 事件风险：减持、解禁、业绩预亏、监管、政策利空必须进入风险。
- 数据缺口：缺少关键数据时降低置信度，不得伪装成确定结论。
- 仓位纪律：输出建议必须带仓位区间或观望条件。
- 复盘要求：保存当时输入和关键证据，便于后续验证。

## 6. 核心数据流

```text
User Request
  -> API Request Validation
  -> Stock Resolver
  -> Analysis Task
  -> Data Context Builder
  -> Quick Agent Router
  -> Deep Research Engine
  -> Risk Review
  -> Report Builder
  -> Report Store
  -> Web/Desktop Display
```

轻量追问不必重新跑完整深度流程。追问优先复用最近一次报告、数据上下文和用户问题，只在数据过期或用户要求重新分析时触发新任务。

## 7. 报告结构

第一阶段报告必须结构化，至少包含：

- 股票名称、代码、分析时间、数据时间范围。
- 总结论：买入、观望、卖出或等待条件。
- 置信度：高、中、低，并解释依据。
- 核心理由：技术面、基本面、资金面、消息面、政策面。
- 风险清单：按严重程度排序。
- 操作建议：入场条件、止损条件、仓位建议、观察指标。
- 数据缺口：哪些关键数据不可用或可能滞后。
- Agent 证据摘要：每个主要 Agent 的核心观点。

## 8. 错误处理

错误处理原则：可降级，但必须显式暴露。

- 单个数据源失败：切换备用源，并记录 provider failure。
- 关键数据缺失：允许生成报告，但必须降低置信度并显示缺口。
- Deep Research Engine 失败：返回快速分析结果和失败原因，不伪装成完整报告。
- LLM 超时或预算不足：输出已完成阶段摘要，标记为 partial report。
- 股票无法解析：要求用户提供更明确代码或名称。

## 9. 测试与验证策略

第一阶段测试重点：

- 股票代码标准化和名称解析。
- 数据 provider adapter 的失败降级。
- 分析任务状态流转。
- Quick Agent 与 Deep Research Engine 的路由判断。
- 报告 schema 校验。
- 风控规则对追高、数据缺口、事件风险的约束。
- API smoke test。

验收标准：

- 不依赖真实 LLM 的离线测试可以通过。
- 至少一个示例股票可以完成端到端 dry run。
- 报告包含结构化结论、风险、证据和数据缺口。
- 失败路径不会静默吞错。

## 10. 架构决策

### 10.1 是否重新开发

结论：重新开发 Money_Never_sleep 平台骨架，但不是重新发明所有能力。

平台骨架、领域模型、API 合约、任务状态、报告 schema 和 Agent adapter 由 Money_Never_sleep 自己定义。参考项目能力通过适配、借鉴和小范围移植进入，而不是整体 fork。

### 10.2 第一优先级模块

第一优先级是 AI 分析模块和 Agent 模块，但它们必须依赖稳定的数据上下文和报告 schema。否则 AI 只会变成提示词堆叠，无法复盘和验证。

### 10.3 桌面端策略

桌面端不作为第一阶段核心。第一阶段先让 Web + API 跑通深度分析闭环。桌面端后续再根据本地能力需求选择技术栈：

- 如果要复用 Web 前端和 Python API，Electron 或 Tauri 更自然。
- 如果要学习 go-stock 的 Wails 本地体验，需要设计 Python 服务与 Go shell 的边界。

## 11. 后续实现计划入口

设计批准后，下一步进入 writing-plans 阶段，创建实现计划。实现计划应优先拆成以下垂直切片：

1. 平台契约和目录骨架。
2. 股票解析与数据上下文 builder。
3. Agent adapter 接口和 mock deep engine。
4. 报告 schema 与存储。
5. 单股分析 API 和最小 Web 页面。
6. TradingAgents-astock 深度引擎接入实验。

## 12. 用户审查点

请重点审查以下决策：

- 是否接受 Money_Never_sleep 自建平台骨架，而不是直接 fork 三个参考项目之一。
- 是否接受 TradingAgents-astock 作为深度 AI 投研引擎优先接入对象。
- 是否接受第一阶段只做单股深度分析闭环，不同时铺开桌面、全市场选股、通知和回测。
- 是否接受报告必须显式展示风险、数据缺口和置信度，而不是只给买卖结论。