# 阶段 5.9：任务超时回收设计

状态：已批准执行
日期：2026-07-01

## 背景

阶段 5.8 已为任务增加取消与重试控制，但如果任务一直卡在非终态，当前系统仍然只能依赖人工取消。缺少统一的超时回收语义，会让 Web/桌面长时间轮询而没有明确结论。

## 目标

1. 为任务记录增加超时参数和开始时间。
2. 让队列在读取或轮询任务时自动将超时的运行中任务标记为 `failed`。
3. 允许 HTTP 创建任务时显式传入 `timeout_s`，不传时使用默认值。

## 非目标

- 不做真正的后台 watchdog 线程。
- 不做自动重试。
- 不做前端超时设置 UI。

## 设计

新增字段：

- `started_at`
- `timeout_s`

默认超时值通过配置给出，例如 `MONEY_TASK_TIMEOUT_S=300`。

超时判定：

- 仅对 `queued` / `quick_screening` / `deep_analysis` / `collecting_data` / `risk_review` 生效。
- 当读取单任务、列最近任务或轮询时，如果任务已超过 `started_at + timeout_s`，则自动更新为 `failed`，错误文案如 `task timed out after 300s`。

## 验收

1. task queue 测试覆盖超时标记。
2. HTTP API 测试覆盖创建带超时任务和读取超时任务。
3. 默认后端测试通过。
4. 文档更新超时语义和限制。