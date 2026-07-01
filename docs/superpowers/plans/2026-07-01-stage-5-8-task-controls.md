# 阶段 5.8：任务取消与重试计划

状态：执行中
日期：2026-07-01

## 任务 1：队列状态机

扩展 `AnalysisTaskRecord` 和队列，支持 `cancelled` 与 `retry_of`。

验证：`test_task_queue.py`

## 任务 2：HTTP 控制端点

新增：

- `POST /tasks/{id}/cancel`
- `POST /tasks/{id}/retry`

验证：`test_http_api.py`

## 任务 3：文档收尾

更新 `README.md`、`docs/stages.md`、`docs/improvement-backlog.md`、`docs/agent-handoff.md`、`docs/information-map.md`。

验证：全量 API 测试、JS 检查、`npm audit --audit-level=high`、`npm run build:mac`。
