# 阶段 5.9：任务超时回收计划

状态：执行中
日期：2026-07-01

## 任务 1：队列与配置

为任务记录增加 `started_at`、`timeout_s`，并引入默认超时配置。

验证：`test_task_queue.py`

## 任务 2：HTTP API

让 `POST /tasks/analysis` 支持 `timeout_s`，并在 `GET /tasks` / `GET /tasks/{id}` 路径上触发超时清理。

验证：`test_http_api.py`

## 任务 3：文档收尾

更新 `README.md`、`docs/stages.md`、`docs/improvement-backlog.md`、`docs/agent-handoff.md`、`docs/information-map.md`。

验证：全量 API 测试、JS 检查、`npm audit --audit-level=high`、`npm run build:mac`。
