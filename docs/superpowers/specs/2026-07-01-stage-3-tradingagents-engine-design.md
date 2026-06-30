# 阶段 3：TradingAgents 深度引擎接入设计规格

日期：2026-07-01
状态：已按用户批准进入设计与计划
阶段：Brainstorming 设计规格，不包含实现代码

## 1. 背景

阶段 1 已经建立单股分析后端契约：`AnalysisService` 通过 `DeepResearchEngine.analyze(task_id, context)` 触发深度分析，并用 `MockDeepResearchEngine` 生成结构化报告。阶段 2 已经完成真实 A 股 quote 数据层的最小切片：`DataContext` 现在包含 quote、technicals、fundamentals、news、gaps 和 diagnostics。

阶段 3 的目标是把 TradingAgents-astock 接入为可选真实深度投研引擎，同时保持 Money_Never_sleep 自己的领域契约稳定。业务层不应直接依赖 TradingAgents 的图对象、LangGraph 状态、模型配置或输出文件结构。

## 2. 设计选项

### 方案 A：直接在 `AnalysisService` 中调用 TradingAgentsGraph

优点是代码最少，能最快跑通真实调用。缺点是服务层会直接依赖 TradingAgents 的包结构、模型配置、异常类型和返回状态，默认测试也更容易被重依赖污染。该方案不推荐。

### 方案 B：在 `DeepResearchEngine` 后增加 adapter 与 runner 协议

Money_Never_sleep 增加 `TradingAgentsDeepResearchEngine`，它只依赖一个小型 runner 协议。runner 负责执行 TradingAgents，并返回标准化原始结果；engine 负责把结果映射成 `AnalysisReport`。默认测试使用 fake runner，不导入真实 TradingAgents。真实 runner 只在显式工厂或 smoke 中启用。该方案推荐。

### 方案 C：先做外部 CLI 子进程集成

通过命令行调用 TradingAgents-astock，避免 Python 依赖冲突。优点是隔离更强；缺点是结构化状态、错误处理、测试和超时控制会更粗糙，后续需要再迁回 Python adapter。该方案作为失败回退，不作为第一版主线。

## 3. 推荐方向

采用方案 B：adapter + runner 协议。

第一版只做可测试的深度引擎接入边界，不默认执行真实 LLM 调用。真实 TradingAgents 调用必须 opt-in，并通过配置或显式工厂启用。默认 API 仍使用 `MockDeepResearchEngine`，保证离线测试稳定。

## 4. 目标

阶段 3 完成后，Money_Never_sleep 应具备：

1. 一个 `TradingAgentsDeepResearchEngine`，实现现有 `DeepResearchEngine` 协议。
2. 一个小型 `TradingAgentsRunner` 协议，隔离真实 TradingAgents-astock 调用。
3. 一个 `TradingAgentsRunResult` 契约，表达 final decision、agent reports、raw state、diagnostics 和失败信息。
4. 一个可测试的 fake runner，用于默认离线测试。
5. 一个真实 runner 壳，按配置懒加载 `tradingagents.graph.trading_graph.TradingAgentsGraph`。
6. API 层新增可选 TradingAgents 服务工厂，默认服务不变。
7. opt-in smoke 测试或命令，用于手动验证真实 TradingAgents 链路。
8. 失败降级：真实 runner 抛错时返回结构化 failed/partial report，而不是拖垮整个分析服务。

## 5. 非目标

阶段 3 第一版不做：

- 不复制 TradingAgents-astock 源码到 Money_Never_sleep。
- 不把 TradingAgents-astock 加入默认必装依赖。
- 不在默认测试中调用真实 LLM 或真实 TradingAgentsGraph。
- 不实现完整 Web/桌面 UI 切换。
- 不实现报告持久化、追问、成本看板或任务队列。
- 不要求 TradingAgents 读取 Money_Never_sleep 的所有 `DataContext` 字段；第一版可以先用股票代码和交易日期触发真实图。

## 6. 边界设计

### 6.1 当前 Money_Never_sleep 边界

现有边界是：

```text
AnalysisService
  -> StockResolver
  -> DataContextBuilder
  -> QuickAgentRouter
  -> DeepResearchEngine
      -> AnalysisReport
```

阶段 3 不改变 `AnalysisService` 的主要职责。真实深度引擎仍通过 `deep_engine.analyze(task_id, context)` 进入。

### 6.2 新增 adapter 边界

建议形成：

```text
TradingAgentsDeepResearchEngine
  -> TradingAgentsRunner 协议
      -> FakeTradingAgentsRunner（离线测试）
      -> TradingAgentsGraphRunner（真实 opt-in）
  -> TradingAgentsRunResult
  -> AnalysisReport
```

`TradingAgentsDeepResearchEngine` 负责：

- 从 `DataContext` 取 `stock.code`、`stock.name`、gaps 和 diagnostics。
- 调用 runner。
- 将 runner 结果映射成 Money_Never_sleep 的 `AnalysisReport`。
- 将 runner 失败映射为 `AnalysisStatus.FAILED` 或低置信度 partial report。

runner 负责：

- 接受标准化请求，不依赖 Money_Never_sleep 的完整服务对象。
- 对真实 TradingAgentsGraph 做懒加载。
- 返回结构化结果，不直接返回 LangGraph 内部对象给业务层。

## 7. 数据契约

### 7.1 TradingAgentsRunRequest

字段建议：

- `task_id`
- `code`
- `name`
- `market`
- `trade_date`
- `context_snapshot`
- `diagnostics`

`context_snapshot` 使用普通 dict，保留 quote、technicals、fundamentals、news 和 gaps，方便后续审计。

### 7.2 TradingAgentsRunResult

字段建议：

- `ok`
- `source`
- `final_decision`
- `summary`
- `agent_reports`
- `raw_state`
- `diagnostics`
- `error_type`
- `error_message`

`agent_reports` 第一版使用 `dict[str, str]`，key 可映射为 market/news/fundamentals/policy/hot_money/lockup/risk 等。

## 8. 配置策略

默认配置保持 mock：

- 默认 API 工厂继续使用 `MockDeepResearchEngine`。
- 新增 `build_tradingagents_analysis_service(...)` 或等价工厂，只有显式调用才启用真实/伪 runner。
- 真实 runner 的 reference path、cache/results 目录、模型 provider 和模型名均来自配置或参数，不写死本机路径、模型名或 secret。
- `.env.example` 仅新增非 secret 的 opt-in 开关和路径示例，不写 API key。

## 9. 错误处理

1. fake runner 永远离线、确定性返回成功结果。
2. 真实 runner import 失败时返回失败结果，`error_type` 为 `ModuleNotFoundError` 或对应异常名。
3. TradingAgentsGraph 执行失败时返回失败结果，并携带 error message。
4. engine 对失败结果生成 `AnalysisReport`，状态为 `FAILED`，action 为 `WATCH`，confidence 为 `LOW`，risks 中包含失败原因。
5. diagnostics 必须保留 `DataContext.data_diagnostics`，并追加 runner diagnostics。

## 10. 测试策略

默认测试离线、确定性：

- fake runner -> engine -> report 映射测试。
- runner 失败 -> failed report 测试。
- API 默认服务仍 mock 测试。
- API TradingAgents 工厂使用 fake runner 测试。
- 真实 runner import/Graph 调用通过 monkeypatch 或 fake graph 测试，不调用网络/LLM。
- 真实 smoke 使用 env marker opt-in，默认 skip。

## 11. 验收标准

阶段 3 实现完成后验收标准为：

1. `services/api/tests` 默认离线测试通过。
2. 默认 API 服务仍使用 mock deep engine。
3. 可选 TradingAgents 服务工厂能通过 fake runner 返回结构化报告。
4. runner 失败时不会抛穿到 API 层，而是形成可序列化 failed report。
5. 文档记录真实 smoke 命令和启用条件。
6. README 或阶段文档更新阶段 3 状态、风险和下一步建议。

## 12. 下一步

使用 writing-plans 创建阶段 3 实现计划。实现计划应拆成小任务：

1. TradingAgents run request/result 契约。
2. TradingAgentsDeepResearchEngine + fake runner。
3. 失败映射与 diagnostics。
4. 真实 TradingAgentsGraphRunner 壳。
5. API 可选工厂与配置入口。
6. opt-in smoke 与文档更新。
