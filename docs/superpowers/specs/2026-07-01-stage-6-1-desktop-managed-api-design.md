# 阶段 6.1：桌面托管本地 API 与运行时服务装配设计

状态：已批准执行
日期：2026-07-01

## 背景

当前桌面端默认只打开离线 Web 工作台；如需真实 HTTP API，用户必须手动启动 Python server 并显式设置 `MNS_DESKTOP_API_URL`。同时，当前 `run_http_server()` 默认装配的是离线 mock service，不足以构成“开箱可用”的本地应用体验。

## 目标

1. 让桌面端在未指定 `MNS_DESKTOP_API_URL` 时，自动尝试托管本地 Python API server。
2. 让 HTTP server 默认使用更接近可用产品的运行时 service：真实腾讯 quote + mock deep engine；并保留切换真实 TradingAgents 的配置入口。
3. 打包后的桌面应用携带 `services/api` 源码资源，使其在本机已有 Python 时可以拉起本地 server。
4. 保持已有离线 mock fallback：server 无法启动时，桌面仍能打开 Web 页面。

## 非目标

- 不把 Python 运行时一起打进 Electron 包。
- 不解决 macOS 签名、公证、DMG。
- 不解决 TradingAgents 真实依赖和 API key 分发。
- 不重做 Web UI。

## 设计

### 运行时 service 装配

新增运行时 factory：

- market data 模式默认使用 `tencent` quote + static fallback。
- deep engine 模式默认使用 `mock`。
- 若环境变量显式指定 `MONEY_DEEP_ENGINE=tradingagents`，则尝试装配 `TradingAgentsGraphRunner`。

### Desktop managed API

Electron 主进程新增：

- 自动检测 Python 可执行文件：优先 `MNS_DESKTOP_PYTHON_BIN`，其次 repo `.venv/bin/python`，再退回 `python3` / `python`。
- 若未设置 `MNS_DESKTOP_API_URL`，则尝试启动本地 server 并等待 `/health` 可用。
- 启动成功后，自动以 `?api=http://127.0.0.1:<port>` 打开 Web 工作台。
- 启动失败时记录日志并回退到离线模式。
- 应用退出时回收本地 server 子进程。

### 打包资源

桌面 `extraResources` 额外携带 `services/api`，供 packaged app 的 Python 进程引用。

## 验收

1. Desktop main/preload/package 测试覆盖自动 server 装配关键字符串或结构。
2. 运行时 service factory 测试覆盖默认模式和环境变量切换。
3. 默认后端测试通过。
4. 桌面 JS 检查通过，macOS `.app` 可构建。
5. README、stages、backlog、handoff、information map 更新。