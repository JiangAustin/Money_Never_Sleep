# 阶段 7.4：回测成本、滑点和复权参数计划

状态：执行中
日期：2026-07-01

## 任务 1：契约扩展

新增 `BacktestOptions`，扩展 `BacktestResult` 字段：`gross_return_pct`、`cost_impact_pct`、`options`。

验证：`test_analysis_contracts.py` round-trip。

## 任务 2：回测引擎

`SimpleBacktestEngine.run(report, prices, options=None)` 支持成本/滑点净收益计算；默认 options 保持原行为。

验证：`test_backtest.py` 增加净收益测试，并确保旧测试不变。

## 任务 3：API 集成

`AnalysisService`、Python API、HTTP API 支持 options；provider 回测同样透传 options。

验证：`test_analysis_api.py`、`test_http_api.py`。

## 任务 4：文档收尾

更新 `README.md`、`docs/stages.md`、`docs/improvement-backlog.md`、`docs/agent-handoff.md`、`docs/information-map.md`。

验证：全量 API 测试、JS 语法检查、macOS desktop build。
