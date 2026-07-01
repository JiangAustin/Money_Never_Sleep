# 阶段 5.15：任务重试策略可观测性

状态：已批准执行
日期：2026-07-01

## 背景

阶段 5.14 已支持指数因子、抖动和 timeout 倍率，但这些策略只体现在 `next_retry_at` 上。调用方无法知道：

1. 本次延迟总秒数是多少。
2. 命中了哪类策略（generic / timeout）。
3. 任务历史里的这次等待是如何得出的。

## 目标

1. 在任务记录里保存最小重试决策信息。
2. HTTP `/tasks` 和 `/tasks/{id}` 自动透出这些字段。
3. Web 最近任务列表展示下一次重试时间和策略命中信息。

## 非目标

- 不改动当前退避算法。
- 不增加前端配置或高级调试面板。
- 不引入新的持久化后端。

## 设计

新增任务记录字段：

- `next_retry_delay_s: int | None`
- `next_retry_policy: str | None`

字段语义：

- `next_retry_delay_s`：本次计划重试最终采用的延迟秒数。
- `next_retry_policy`：当前命中的策略标签，先支持 `generic` 和 `timeout`。

实现方式：

- `_compute_retry_delay_s(...)` 返回 `(delay_s, policy)`。
- `_maybe_retry(...)` 在首次计划重试时同时写入 `next_retry_at`、`next_retry_delay_s`、`next_retry_policy`。
- 子重试任务创建后不回写父任务，保留原计划信息供历史观察。

## 验收

1. task queue / HTTP API / Web 契约测试覆盖新增字段。
2. API 全量测试通过。
3. 文档同步到 5.15。