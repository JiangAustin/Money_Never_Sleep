# 阶段 5.7：任务持久化与恢复计划

状态：执行中
日期：2026-07-01

## 任务 1：任务 repository

新增任务 record/repository 和 JSON 文件实现。

验证：新增 `test_task_queue.py` 或相关 repository 测试。

## 任务 2：队列恢复逻辑

让 task queue 支持注入 repository，并在初始化时恢复未完成任务。

验证：重启语义测试。

## 任务 3：HTTP API 列表接口

新增 `GET /tasks?limit=`，并让默认 HTTP app 使用 JSON task repository。

验证：`test_http_api.py`

## 任务 4：文档收尾

更新 `README.md`、`apps/web/README.md`、`docs/stages.md`、`docs/improvement-backlog.md`、`docs/agent-handoff.md`、`docs/information-map.md`。

验证：全量 API 测试、JS 检查、`npm audit --audit-level=high`、`npm run build:mac`。
