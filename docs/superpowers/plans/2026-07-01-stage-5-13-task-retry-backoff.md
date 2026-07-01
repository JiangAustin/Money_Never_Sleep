# 阶段 5.13：任务重试退避策略计划

状态：已完成
日期：2026-07-01

## 任务 1：测试先行

扩展 `services/api/tests/test_task_queue.py`：

- 失败任务会写入 `next_retry_at`
- watchdog 到点前不派生 retry task
- watchdog 到点后派生 retry task

## 任务 2：实现退避调度

更新 `services/api/money_api/domains/analysis/task_queue.py`：

- 增加退避配置参数
- 增加 `next_retry_at` 字段和序列化
- 修改 `_maybe_retry` 为“计划重试 + 到点执行”

## 任务 3：文档收尾

更新 `README.md`、`docs/stages.md`、`docs/improvement-backlog.md`、`docs/agent-handoff.md`、`docs/information-map.md`。

验证：

- `PYTHONPATH=services/api ... pytest services/api/tests -q`
- `node --check` 四个入口
- `npm audit --audit-level=high`
- `npm run build:mac`