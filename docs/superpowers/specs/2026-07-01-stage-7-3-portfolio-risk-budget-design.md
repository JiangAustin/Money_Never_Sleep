# 阶段 7.3：组合风险预算设计

状态：已批准执行
日期：2026-07-01

## 背景

阶段 7 已为单份分析报告生成风控纪律，阶段 7.1/7.2 已让报告可被价格序列回测。当前缺口是系统仍然只看单股，无法回答“多份报告合在一起时总仓位是否过高、单票是否过度集中”。

## 目标

1. 建立组合风险预算的稳定领域契约。
2. 基于已有 `AnalysisReport.risk_controls.max_position_pct` 计算建议组合仓位。
3. 输出总仓位、现金保留、单票预算和风险规则。
4. 暴露 Python API 和 HTTP API，供 Web/Desktop 后续接入。

## 非目标

- 不接真实券商账户或持仓同步。
- 不做行业、主题、相关性或波动率模型。
- 不做自动调仓或交易指令。
- 不做 UI 组合页。

## 设计

新增 `PortfolioPositionBudget` 和 `PortfolioRiskBudget`：

- `PortfolioPositionBudget`：单只股票的预算结果，包含 task/report、股票、建议仓位、动作、置信度和规则说明。
- `PortfolioRiskBudget`：组合层结果，包含总仓位、现金保留、单票上限、持仓预算列表、组合规则和免责声明。

新增纯领域服务 `PortfolioRiskBudgeter`：

- 输入：一组 `AnalysisReport`。
- 单票预算：优先使用 `report.risk_controls.max_position_pct`，没有风控计划时按 0 处理并记录规则。
- 单票上限：默认 20%。
- 组合总仓位上限：默认 60%。
- 若单票合计超过组合总上限，按比例压缩所有正仓位预算。
- `sell`、`failed`、风险计划为 0 的报告自然得到 0 仓位。

## 验收

1. 契约 round-trip 测试通过。
2. 预算器可处理正常、多报告压缩、缺失风控计划、空组合。
3. Python API 和 HTTP API 均可从已有报告历史生成组合预算。
4. 默认离线测试通过。
5. 文档记录完成状态、限制和下一步。
