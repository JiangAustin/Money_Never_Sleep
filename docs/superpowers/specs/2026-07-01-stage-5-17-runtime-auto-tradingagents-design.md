# 阶段 5.17：runtime 默认深度引擎 auto 模式

状态：已批准执行
日期：2026-07-01

## 背景

当前 runtime service 虽已具备真实行情与真实新闻输入，但默认深度引擎仍是 `mock`。这意味着默认路径不会优先尝试真实 TradingAgents，多 Agent 投研链路仍停留在显式 opt-in。

## 目标

1. 将 runtime 默认深度引擎语义从 `mock` 推进到 `auto`。
2. `auto` 模式下优先尝试真实 TradingAgents，失败时自动回退 mock，不能影响默认可用性。
3. 同步桌面托管 API 默认值和 `.env.example`。

## 非目标

- 不在本阶段解决 LLM/API key 配置、模型成本或完整生产部署。
- 不改变显式 `MONEY_DEEP_ENGINE=tradingagents` 的直连语义。
- 不实现新的前端 UI 开关。

## 设计

新增 `AutoFallbackDeepResearchEngine`：

- primary: `TradingAgentsDeepResearchEngine`
- fallback: `MockDeepResearchEngine`

行为：

1. primary 成功：直接返回真实 TradingAgents 报告。
2. primary 失败：保留失败 diagnostics，再回退到 mock 报告。
3. fallback 报告必须是 `report_ready`，并明确写出已回退原因。

runtime 装配：

- `MONEY_DEEP_ENGINE=auto`：使用 auto 引擎
- `MONEY_DEEP_ENGINE=mock`：保持 mock
- `MONEY_DEEP_ENGINE=tradingagents`：保持纯真实引擎
- 默认值改为 `auto`

补充：

- `TradingAgentsGraphRunner` 尝试按 `TRADINGAGENTS_ASTOCK_PATH` 加入导入路径，提升默认成功率。

## 验收

1. runtime 默认模式在注入 fake runner 时走真实 TradingAgents。
2. runtime 默认模式在注入 failing runner 时自动回退 mock。
3. `.env.example` 与桌面托管默认值同步为 `auto`。
4. 全量 API 测试通过。