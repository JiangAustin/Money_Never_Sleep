# 阶段 7：风控纪律层设计规格

日期：2026-07-01
状态：已按用户批准进入设计与计划
阶段：Brainstorming 设计规格，不包含实现代码

## 1. 背景

当前系统已能生成单股分析报告、保存历史、通过 HTTP/Web/Desktop 查看结果。但报告里的 `action` 和 `confidence` 仍偏结论表达，缺少统一的风险纪律：仓位上限、止损纪律、止盈纪律、数据缺口降级和投资免责声明。

阶段 7 完整目标包含风控、回测和组合。第一版先做“风控纪律层”，把每份报告约束为可复盘、可解释、不过度荐股的结构化输出。回测和组合留到后续切片。

## 2. 推荐方向

新增 `RiskControlPlan` 契约和 `DefaultRiskPolicy`。`AnalysisService` 在生成报告后应用风控策略，把风险控制计划写入 `AnalysisReport`。默认策略是确定性的、离线可测的规则系统，不依赖 LLM。

## 3. 目标

阶段 7 第一版完成后应具备：

1. `RiskControlPlan` 和 `RiskControlRule` 可序列化、可恢复。
2. `AnalysisReport.to_dict()` 输出 `risk_controls`。
3. 默认风控策略基于 `status`、`action`、`confidence`、`data gaps` 生成仓位和规则。
4. `AnalysisService` 默认给深度/轻量报告都附加风控计划。
5. Web mock 可展示或至少兼容 `risk_controls` 字段。
6. 文档记录这不是投资建议，只是纪律化输出。

## 4. 非目标

第一版不做：

- 不做历史回测引擎。
- 不做组合层仓位优化。
- 不接真实账户或交易接口。
- 不做自动买卖。
- 不承诺收益或投资建议。

## 5. 风控规则

默认策略：

- `FAILED` 报告：`max_position_pct = 0`。
- `LOW` 置信度：仓位上限 `0.05`。
- `MEDIUM` 置信度：仓位上限 `0.10`。
- `HIGH` 置信度：仓位上限 `0.20`。
- 存在 data gaps：仓位上限不超过 `0.05`，并追加数据缺口规则。
- `SELL`：仓位上限 `0`。
- `WAIT`：仓位上限不超过 `0.03`。
- 默认止损 `0.08`，止盈 `0.15`。
- 所有报告带固定免责声明。

## 6. 测试策略

- 契约 round-trip 测试。
- 默认策略对 medium/low/gaps/failed/sell 的规则测试。
- `AnalysisService` 生成报告后包含 `risk_controls`。
- API 序列化返回 `risk_controls`。
- Web mock 字段兼容测试。
- 全量测试与 JS 语法检查。

## 7. 验收标准

1. 所有报告 payload 包含 `risk_controls`。
2. 风控计划可序列化和恢复。
3. 数据缺口和失败报告会降低或清零仓位。
4. 文档记录风控纪律层的边界和非投资建议声明。
5. 默认测试通过。

## 8. 下一步

后续可继续：

1. 回测接口。
2. 组合层风险预算。
3. 报告复盘结果记录。
4. Web 风控面板和图表。
