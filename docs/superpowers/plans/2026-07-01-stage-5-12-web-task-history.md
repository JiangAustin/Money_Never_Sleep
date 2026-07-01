# 阶段 5.12：Web 任务历史视图计划

状态：执行中
日期：2026-07-01

## 任务 1：测试先行

扩展 `test_web_workbench.py`，覆盖：

- 任务历史区域 DOM 入口
- 获取和渲染任务历史的函数边界

## 任务 2：前端实现

更新 `apps/web/index.html`、`apps/web/src/app.js`、必要时 `apps/web/src/styles.css`：

- 增加最近任务区域
- 调用 `GET /tasks?limit=`
- 在任务相关操作后刷新任务历史

## 任务 3：文档收尾

更新 `apps/web/README.md`、`README.md`、`docs/stages.md`、`docs/agent-handoff.md`、`docs/information-map.md`。

验证：Web 测试、全量 API 测试、JS 检查、`npm audit --audit-level=high`、`npm run build:mac`。