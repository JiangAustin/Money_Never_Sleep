# 阶段 7.4：回测成本、滑点和复权参数设计

状态：已批准执行
日期：2026-07-01

## 背景

阶段 7.1/7.2 已能用传入价格序列或 Sina K 线 provider 回测报告，但收益仍是裸价格涨跌，容易高估实际结果。当前切片补充交易成本、滑点和复权标记，让回测结果表达更接近真实交易约束。

## 目标

1. 新增回测参数契约，支持交易成本、滑点和复权标记。
2. 回测结果保留原始 entry/exit price，同时输出净收益、成本影响和参数回显。
3. Python API 和 HTTP API 可传入成本参数。
4. 默认不传参数时保持现有行为。

## 非目标

- 不实现真实前复权/后复权价格转换。
- 不接券商费率表、印花税细分或最小佣金。
- 不做多次调仓、分批成交或成交量约束。

## 设计

新增 `BacktestOptions`：

- `cost_pct`：单边交易成本，默认 0。
- `slippage_pct`：单边滑点，默认 0。
- `adjustment`：`none`、`qfq`、`hfq` 之一，当前仅记录语义，不转换价格。

净收益计算：

- 多头入场有效价格 = `entry_price * (1 + cost_pct + slippage_pct)`。
- 多头出场有效价格 = `exit_price * (1 - cost_pct - slippage_pct)`。
- `return_pct` 改为净收益。
- 新增 `gross_return_pct` 保存裸价格收益。
- 新增 `cost_impact_pct = return_pct - gross_return_pct`。

## 验收

1. `BacktestOptions` 和扩展后的 `BacktestResult` round-trip 通过。
2. 不传 options 的既有测试结果不变。
3. 传入成本/滑点后净收益低于裸收益，并保留成本影响。
4. HTTP `POST /reports/{task_id}/backtest` 可接受 `options`。
5. 默认离线测试通过。
