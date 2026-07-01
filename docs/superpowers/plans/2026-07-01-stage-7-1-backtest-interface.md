# 阶段 7.1 回测接口实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 让已生成报告可以基于传入价格序列执行确定性回测，输出收益、最大回撤、退出原因和持有天数。

**架构：** 在 analysis contracts 中增加回测契约；新增 `SimpleBacktestEngine`；AnalysisService 暴露 `backtest_report()`；Python API 和 HTTP API 转发；Web mock 加入 backtest 示例字段。

**技术栈：** Python dataclasses、pytest、现有标准库 HTTP dispatcher、浏览器 JavaScript mock 数据。

---

## 任务 1：回测契约

**文件：**

- 修改：`services/api/money_api/domains/analysis/contracts.py`
- 修改：`services/api/tests/test_analysis_contracts.py`

步骤：先写 `BacktestPricePoint` / `BacktestResult` round-trip 失败测试，再实现契约并提交。

## 任务 2：确定性回测引擎

**文件：**

- 创建：`services/api/money_api/domains/analysis/backtest.py`
- 创建：`services/api/tests/test_backtest.py`

步骤：测试止损、止盈、时间退出、最大回撤和价格点不足，再实现 `SimpleBacktestEngine.run(report, prices)` 并提交。

## 任务 3：Service / Python API / HTTP API 集成

**文件：**

- 修改：`services/api/money_api/domains/analysis/service.py`
- 修改：`services/api/money_api/api/v1/router.py`
- 修改：`services/api/money_api/main.py`
- 修改：`services/api/money_api/api/http.py`
- 修改：`services/api/tests/test_analysis_api.py`
- 修改：`services/api/tests/test_http_api.py`

步骤：测试 `backtest_analysis_report(task_id, prices)` 和 `POST /reports/{task_id}/backtest`，再实现并提交。

## 任务 4：Web mock 和文档收尾

**文件：**

- 修改：`apps/web/src/mockData.js`
- 修改：`services/api/tests/test_web_workbench.py`
- 修改：`README.md`
- 修改：`docs/stages.md`
- 修改：`docs/improvement-backlog.md`
- 修改：`docs/agent-handoff.md`
- 修改：`docs/information-map.md`

步骤：Web mock 加 `backtest` 示例，文档标记阶段 7.1 完成并记录验证；运行全量测试、JS 检查和 macOS 构建后提交。

## 自检结果

- 覆盖 backlog `MNS-BL-018`。
- 不接真实行情，价格序列由调用者传入。
- 不做组合回测、交易成本、滑点或复权。
