# 阶段 5.10：任务 watchdog 与自动重试设计

状态：已批准执行
日期：2026-07-01

## 背景

阶段 5.9 已让超时任务在读取时自动失败，但如果前端没有继续轮询，超时不会被主动收敛；同时失败任务仍需人工调用 retry，缺少最小自动重试能力。

## 目标

1. 为任务队列增加后台 watchdog 线程，定期扫描并回收超时任务。
2. 为任务增加 `max_retries` / `retry_count`，在可重试失败时自动重试一次或多次。
3. 保持切片最小：不做复杂调度器，不做指数退避。

## 非目标

- 不做分布式队列。
- 不做跨进程 worker。
- 不做自动重试的前端可视化按钮。

## 设计

新增字段：

- `retry_count`
- `max_retries`

watchdog：

- `InMemoryAnalysisTaskQueue.start_watchdog(interval_s)` 启动后台线程。
- watchdog 周期性遍历任务并调用超时检查。

自动重试：

- 当任务由于超时或执行异常失败，且 `retry_count < max_retries`，自动创建新的 retry task。
- 新任务 `retry_of` 指向原任务；原任务保留 failed。
- 默认 `max_retries=0`，需显式启用。

## 验收

1. task queue 测试覆盖 watchdog 超时回收和自动重试。
2. HTTP API 测试覆盖创建带 `max_retries` 的任务。
3. 默认后端测试通过。
4. 文档更新 watchdog/自动重试语义和限制。