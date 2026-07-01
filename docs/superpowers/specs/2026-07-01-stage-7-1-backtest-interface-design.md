# 阶段 7.1：回测接口设计规格

日期：2026-07-01
状态：已按用户指令继续执行
阶段：设计规格，不包含实现代码

## 1. 背景

阶段 7 第一版已经让每份 `AnalysisReport` 带有 `risk_controls`。但这仍然只是纪律字段，尚不能回答“这条建议按纪律执行后表现如何”。阶段 7.1 的目标是建立最小确定性回测接口，让报告可以用本地价格序列复盘。

## 2. 推荐方向

新增 `BacktestPricePoint`、`BacktestRequest`、`BacktestResult` 和 `SimpleBacktestEngine`。第一版不接真实行情、不做复杂撮合，只接受调用者传入的收盘价序列，并按报告中的止损/止盈纪律计算退出原因、收益率、最大回撤和持有天数。

## 3. 目标

1. 可序列化的回测请求和结果契约。
2. 确定性回测引擎。
3. Python API：`backtest_analysis_report(task_id, prices)`。
4. HTTP API：`POST /reports/{task_id}/backtest`。
5. Web mock 中包含 backtest 示例字段，方便后续展示。
6. 文档更新阶段、台账、交接和信息地图。

## 4. 非目标

- 不接真实 K 线 provider。
- 不做组合回测。
- 不做交易成本、滑点、分红复权。
- 不做异步任务。
- 不做自动交易。

## 5. 规则

- entry price 使用价格序列第一天 close。
- 从第二个价格点开始检查止损/止盈。
- 若收益率小于等于 `-stop_loss_pct`，退出原因 `stop_loss`。
- 若收益率大于等于 `take_profit_pct`，退出原因 `take_profit`。
- 如果没有触发，使用最后一个价格点，退出原因 `time_exit`。
- 最大回撤按 entry 后的最低收益率计算。
- 少于 2 个价格点返回错误。

## 6. 验收标准

1. 回测契约 round-trip 通过。
2. 止损、止盈、时间退出、最大回撤测试通过。
3. Python API 和 HTTP API 可调用。
4. 默认测试、JS 检查、macOS 构建通过。
5. 文档记录后续真实行情、交易成本、组合回测仍待做。
