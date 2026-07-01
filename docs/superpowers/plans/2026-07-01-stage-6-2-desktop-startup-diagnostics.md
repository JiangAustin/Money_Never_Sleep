# 阶段 6.2：桌面启动诊断计划

状态：执行中
日期：2026-07-01

## 任务 1：主进程与 preload

扩展 Electron main / preload：

- 构建 startup 上下文
- 通过 additionalArguments 注入
- preload 解析并暴露给 renderer

验证：`test_desktop_shell.py`

## 任务 2：Web 工作台展示

更新 `apps/web/index.html` 和 `apps/web/src/app.js`：

- mode pill 动态展示
- diagnostics 面板新增 startup section
- 浏览器直接打开时提供合理默认值

验证：`test_web_workbench.py` 和 JS 检查

## 任务 3：文档收尾

更新 `apps/desktop/README.md`、`README.md`、`docs/stages.md`、`docs/agent-handoff.md`、`docs/information-map.md`。

验证：全量 API 测试、JS 检查、`npm audit --audit-level=high`、`npm run build:mac`。
