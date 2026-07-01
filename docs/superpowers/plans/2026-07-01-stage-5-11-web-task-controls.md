# 阶段 5.11：Web 任务控制 UI 计划

状态：执行中
日期：2026-07-01

## 任务 1：测试先行

扩展 `test_web_workbench.py`，覆盖：

- 任务控制按钮区域
- cancel/retry 函数边界

## 任务 2：前端实现

更新 `apps/web/index.html`、`apps/web/src/app.js`、必要时 `apps/web/src/styles.css`：

- 展示当前任务状态与任务 ID
- 提供取消和重试按钮
- 接入现有 HTTP `/tasks/{id}/cancel` 与 `/tasks/{id}/retry`

## 任务 3：文档收尾

更新 `apps/web/README.md`、`README.md`、`docs/stages.md`、`docs/agent-handoff.md`、`docs/information-map.md`。

验证：JS 检查、全量 API 测试、`npm audit --audit-level=high`、`npm run build:mac`。