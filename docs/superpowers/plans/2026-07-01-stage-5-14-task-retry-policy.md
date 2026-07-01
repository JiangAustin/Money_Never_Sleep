# 阶段 5.14：任务重试策略细化计划

状态：已完成
日期：2026-07-01

## 任务 1：测试先行

扩展 `services/api/tests/test_task_queue.py`：

- timeout 失败可应用倍率与抖动
- 默认配置下原有行为不变

## 任务 2：实现策略增强

更新 `services/api/money_api/domains/analysis/task_queue.py`：

- 增加策略参数和可控随机源
- 扩展延迟计算函数，支持错误类型倍率和抖动

## 任务 3：验证与文档

- 运行 API 测试、脚本语法检查、macOS 构建
- 更新 `docs/stages.md`、`docs/improvement-backlog.md`、`docs/agent-handoff.md`、`docs/information-map.md`、`README.md`
- 合并推送并清理 worktree