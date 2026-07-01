# 阶段 5.15：任务重试策略可观测性计划

状态：执行中
日期：2026-07-01

## 任务 1：测试先行

扩展：

- `services/api/tests/test_task_queue.py`
- `services/api/tests/test_http_api.py`
- `services/api/tests/test_web_workbench.py`

覆盖：

- 任务记录包含 `next_retry_delay_s` 和 `next_retry_policy`
- HTTP `/tasks` 返回这些字段
- Web 任务历史渲染包含下一次重试信息

## 任务 2：实现

更新：

- `services/api/money_api/domains/analysis/task_queue.py`
- `apps/web/src/app.js`

## 任务 3：验证与收尾

- 运行 API 测试、Web 契约测试、Node 语法检查、macOS 构建
- 更新阶段文档、backlog、handoff、README
- 合并、推送、清理