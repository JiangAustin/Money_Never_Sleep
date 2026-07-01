# 阶段 5.14：任务重试策略细化（抖动 + 错误类型倍率）

状态：已批准执行
日期：2026-07-01

## 背景

阶段 5.13 已实现延迟重试与指数退避，但仍存在两个能力缺口：

1. 退避间隔固定，缺少抖动，不利于避免同类任务同秒重试。
2. 不区分失败类型，超时类故障和普通失败使用同一延迟策略。

## 目标

1. 增加可配置的退避策略参数：指数因子、抖动比例、超时倍率。
2. 保持默认行为兼容（默认参数下语义不变）。
3. 在任务记录中继续沿用 `next_retry_at`，不新增破坏性字段。

## 非目标

- 不引入复杂策略引擎。
- 不增加数据库或分布式调度器。
- 不新增前端配置界面。

## 设计

队列新增参数：

- `retry_backoff_factor`（默认 2）
- `retry_jitter_ratio`（默认 0.0，表示关闭抖动）
- `retry_timeout_multiplier`（默认 1）

延迟计算：

1. 基础延迟：`base = retry_backoff_base_s * retry_backoff_factor^retry_count`
2. 错误倍率：若错误文案包含 `timeout`，`base *= retry_timeout_multiplier`
3. 上限：`base = min(base, retry_backoff_max_s)`
4. 抖动：`jitter = int(base * retry_jitter_ratio * random)`，最终延迟 `min(retry_backoff_max_s, base + jitter)`

## 验收

1. 测试覆盖抖动与 timeout 倍率组合行为（可控随机源）。
2. 现有队列测试和 API 测试保持通过。
3. 阶段文档和 backlog 同步到 5.14。