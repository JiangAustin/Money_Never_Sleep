# 阶段 7.3：组合风险预算计划

状态：执行中
日期：2026-07-01

## 任务 1：领域契约

新增 `PortfolioPositionBudget` 和 `PortfolioRiskBudget`，支持 `to_dict/from_dict`。

验证：`test_analysis_contracts.py` 增加 round-trip。

## 任务 2：预算器

新增 `portfolio_risk.py`，实现 `PortfolioRiskBudgeter.build(reports)`。

规则：

- 缺失 `risk_controls` 的报告仓位为 0。
- 单票预算不超过 `max_single_position_pct`。
- 总仓位不超过 `max_total_position_pct`。
- 超过总仓位时按比例压缩正仓位。
- 空组合返回 0 总仓位和 100% 现金。

验证：新增 `test_portfolio_risk.py`。

## 任务 3：API 暴露

在 `AnalysisService`、Python router、public main 和 HTTP API 增加组合预算入口。

建议 HTTP 路径：`POST /portfolio/risk-budget`，body 可选 `{ "task_ids": [...] }`；未传时使用最近报告。

验证：更新 `test_api.py` / `test_http_api.py`。

## 任务 4：文档收尾

更新 `README.md`、`docs/stages.md`、`docs/improvement-backlog.md`、`docs/agent-handoff.md`、`docs/information-map.md`。

验证：全量 API 测试、JS 语法检查、macOS desktop build。
