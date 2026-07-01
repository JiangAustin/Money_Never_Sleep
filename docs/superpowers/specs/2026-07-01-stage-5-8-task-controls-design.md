# 阶段 5.8：任务取消与重试设计

状态：已批准执行
日期：2026-07-01

## 背景

阶段 5.7 已让 HTTP 任务可持久化和恢复，但任务仍然缺少最基本的控制面：用户无法取消一个排队中的任务，也无法基于失败/取消的任务重新发起一次相同分析。

## 目标

1. 为 HTTP 任务增加取消接口。
2. 为失败或已取消任务增加重试接口。
3. 保持实现最小，不引入真正的线程中断或复杂 worker 管理。

## 非目标

- 不实现底层 Python 调用或外部 LLM 请求的强制中断。
- 不做自动重试策略。
- 不做前端任务按钮 UI。

## 设计

新增任务状态：`cancelled`。

新增 HTTP 端点：

- `POST /tasks/{task_id}/cancel`
- `POST /tasks/{task_id}/retry`

语义：

- cancel：如果任务仍处于非终态，标记为 `cancelled`，记录 `cancelled by user`。
- retry：仅允许 `failed` 或 `cancelled` 任务；新建一个任务，复用原 `symbol/message`，并记录 `retry_of`。
- 对已经被取消的任务，后台线程完成后不得再把状态改回 `report_ready`；即使底层分析已经跑完，任务状态仍保留 `cancelled`。

## 验收

1. task queue 测试覆盖 cancel/retry。
2. HTTP API 测试覆盖 cancel/retry 端点和无效状态。
3. 默认后端测试通过。
4. 文档记录该控制面的限制：取消不是强制中断。