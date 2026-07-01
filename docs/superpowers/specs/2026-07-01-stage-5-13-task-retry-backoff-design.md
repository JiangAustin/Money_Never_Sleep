# 阶段 5.13：任务重试退避策略设计

状态：已批准执行
日期：2026-07-01

## 背景

阶段 5.10 已支持自动重试，但失败后会立即派生 retry task。缺少最小退避会带来两个问题：

1. 瞬时故障时可能快速打满重试次数。
2. 用户无法在任务历史中看出“何时会重试”。

## 目标

1. 给自动重试增加最小指数退避策略。
2. 在任务记录中显式保存下一次可重试时间。
3. 保持已有 API 契约兼容，不破坏现有任务状态流。

## 非目标

- 不引入分布式队列。
- 不做复杂抖动策略。
- 不做可配置 UI。

## 设计

新增字段（任务记录）：

- `next_retry_at: str | None`

新增队列策略：

- `retry_backoff_base_s`（默认 2s）
- `retry_backoff_max_s`（默认 30s）

退避公式：

- `delay = min(retry_backoff_max_s, retry_backoff_base_s * 2^retry_count)`

语义：

- 当任务失败且仍可重试时，不立即派生新任务。
- 先更新失败任务的 `next_retry_at`。
- watchdog 在 `now >= next_retry_at` 时再派生 retry task。

## 验收

1. `test_task_queue.py` 覆盖 `next_retry_at` 与退避调度。
2. 全量 API 测试通过。
3. 文档更新阶段结论和已知限制。