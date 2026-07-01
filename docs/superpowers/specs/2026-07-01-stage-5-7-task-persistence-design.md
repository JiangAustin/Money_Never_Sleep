# 阶段 5.7：任务持久化与恢复设计

状态：已批准执行
日期：2026-07-01

## 背景

阶段 5.6 已为 HTTP API 和 Web 工作台补齐异步任务队列与状态轮询，但当前任务记录全在内存中。服务一重启，前端轮询和近期任务上下文都会丢失，也无法区分“已完成的历史任务”和“重启时中断的任务”。

## 目标

1. 为分析任务增加 JSON 文件持久化。
2. 服务启动时可读取历史任务。
3. 对重启前仍处于运行态的任务，恢复时标记为失败并写明原因。
4. 增加近期任务查询接口，便于 Web/Desktop 后续展示任务历史。

## 非目标

- 不做真正的断点恢复执行。
- 不做取消、重试和并发限流。
- 不引入 SQLite 或外部数据库。

## 设计

新增任务 repository：

- `InMemoryAnalysisTaskRepository`
- `JsonFileAnalysisTaskRepository`

任务文件格式按 `task_id.json` 存放，字段保持与 HTTP task record 一致。

恢复策略：

- 启动时读取所有任务。
- 若任务状态是 `queued` / `quick_screening` / `deep_analysis` / `risk_review` / `collecting_data`，说明上次执行中断，恢复时统一改成 `failed`，错误文案例如“service restarted before task finished”。

HTTP API：

- `GET /tasks?limit=20`：返回最近任务。
- `GET /tasks/{id}`：继续支持单任务查询。

默认 runtime server 使用 JSON task repository，目录放在 `data/cache/tasks`。

## 验收

1. repository 测试覆盖 save/get/list 与恢复中断任务语义。
2. HTTP API 测试覆盖 `GET /tasks` 和重启后仍能查到任务。
3. 默认后端测试通过。
4. JS 语法检查通过，macOS `.app` 可构建。
5. 文档更新任务持久化和剩余缺口。