# 阶段 5.17：runtime 默认深度引擎 auto 模式计划

状态：执行中
日期：2026-07-01

## 任务 1：测试先行

扩展：

- `services/api/tests/test_analysis_api.py`
- `services/api/tests/test_tradingagents_engine.py`

覆盖：

- runtime 默认 deep engine 走 auto
- auto 模式成功时使用真实 TradingAgents 结果
- auto 模式失败时回退 mock，并保留失败 diagnostics

## 任务 2：实现

更新：

- `services/api/money_api/domains/analysis/tradingagents_engine.py`
- `services/api/money_api/integrations/tradingagents_runner.py`
- `services/api/money_api/api/v1/router.py`
- `.env.example`
- `apps/desktop/src/main.js`
- `apps/desktop/README.md`

## 任务 3：验证与收尾

- 运行 API 测试、Python 编译检查、Node 语法检查、macOS 构建
- 更新阶段文档、backlog、handoff、README
- 合并、推送、清理