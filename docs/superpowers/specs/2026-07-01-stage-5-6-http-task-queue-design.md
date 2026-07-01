# 阶段 5.6：HTTP 任务队列与状态轮询设计

状态：已批准执行
日期：2026-07-01

## 背景

当前 Web 工作台和桌面壳都通过同步 `POST /analysis` 发起分析。对于 mock 或轻量查询，这没问题；但真实深度分析路径会变成长请求，前端无法稳定展示“排队/执行中/完成/失败”。

## 目标

1. 为 HTTP API 增加异步任务入口和状态轮询。
2. Web 工作台改为优先使用任务模式，并在完成后自动拉取最终报告。
3. 保留现有同步 `POST /analysis`，避免破坏已有调用方。
4. 使用标准库和最小线程模型，不引入外部队列依赖。

## 非目标

- 不做持久化任务队列。
- 不做任务取消、重试或并发限流配置。
- 不做前端框架迁移。

## 设计

新增 HTTP 任务契约：

- `POST /tasks/analysis`：创建任务，返回 `202` 和任务记录。
- `GET /tasks/{task_id}`：返回任务状态。

任务记录字段：

- `task_id`
- `symbol`
- `message`
- `status`
- `created_at`
- `updated_at`
- `report_id`
- `error`

执行模型：

- 创建任务后，在后台线程调用 `AnalysisService.create_single_stock_analysis()`。
- 状态最小闭环：`queued -> quick_screening|deep_analysis -> report_ready|failed`。
- 当任务完成时记录 `report_id`；前端可再通过 `/reports/{report_id}` 拉完整报告。

Web 工作台：

- 有 `apiBaseUrl` 时，优先 `POST /tasks/analysis`。
- 轮询 `/tasks/{id}`，直到 `report_ready` 或 `failed`。
- 成功时拉最终报告；失败时生成 fallback 报告并带任务错误诊断。
- 在提交按钮附近显示任务状态文本。

## 验收

1. HTTP API 测试覆盖创建任务、轮询状态、失败输入校验。
2. Web workbench 测试覆盖任务模式函数和状态展示入口。
3. 默认后端测试通过。
4. JS 语法检查通过，macOS `.app` 可构建。
5. 文档更新任务模式说明和限制。