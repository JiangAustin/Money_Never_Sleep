# 阶段 5.10：任务 watchdog 与自动重试计划

状态：执行中
日期：2026-07-01

## 任务 1：队列字段与 watchdog

为任务记录增加 `retry_count` / `max_retries`，并实现后台 watchdog 扫描。

验证：`test_task_queue.py`

## 任务 2：自动重试语义

在超时或执行失败时，根据 `max_retries` 自动派生 retry task。

验证：`test_task_queue.py`、`test_http_api.py`

## 任务 3：HTTP 任务创建参数

让 `POST /tasks/analysis` 支持 `max_retries`。

验证：`test_http_api.py`

## 任务 4：文档收尾

更新 `README.md`、`docs/stages.md`、`docs/improvement-backlog.md`、`docs/agent-handoff.md`、`docs/information-map.md`。

验证：全量 API 测试、JS 检查、`npm audit --audit-level=high`、`npm run build:mac`。
