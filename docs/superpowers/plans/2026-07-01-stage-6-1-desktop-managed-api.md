# 阶段 6.1：桌面托管本地 API 与运行时服务装配计划

状态：执行中
日期：2026-07-01

## 任务 1：运行时 service factory

在 API 装配层新增运行时 factory，并让 `run_http_server()` 默认使用该 factory。

验证：新增 `test_analysis_api.py` 或新测试文件，覆盖默认 runtime 模式和 env 切换。

## 任务 2：Desktop managed API

扩展 Electron main：

- 探测 Python
- 探测/选择本地 API URL
- 自动启动 server
- 等待 health
- 退出时回收子进程

验证：扩展 `test_desktop_shell.py` 的结构性断言。

## 任务 3：打包资源与文档

更新 `apps/desktop/package.json` extraResources，更新 `apps/desktop/README.md` 和仓库级文档。

验证：全量 API 测试、JS 语法检查、`npm audit --audit-level=high`、`npm run build:mac`。
