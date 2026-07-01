# 阶段 5.6：HTTP 任务队列与状态轮询计划

状态：执行中
日期：2026-07-01

## 任务 1：任务存储与执行器

新增内存任务记录和后台执行器。

验证：新增测试覆盖任务状态流转。

## 任务 2：HTTP API 接口

新增：

- `POST /tasks/analysis`
- `GET /tasks/{task_id}`

保留现有同步 `POST /analysis`。

验证：`test_http_api.py`

## 任务 3：Web 工作台轮询

有 `apiBaseUrl` 时，改用任务模式并轮询状态；无 `apiBaseUrl` 时保留本地 mock。

验证：`test_web_workbench.py` 和 JS 检查。

## 任务 4：文档收尾

更新 `README.md`、`docs/stages.md`、`docs/improvement-backlog.md`、`docs/agent-handoff.md`、`docs/information-map.md`。

验证：全量 API 测试、JS 检查、`npm audit --audit-level=high`、`npm run build:mac`。
