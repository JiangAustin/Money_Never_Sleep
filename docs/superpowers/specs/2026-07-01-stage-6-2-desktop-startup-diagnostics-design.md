# 阶段 6.2：桌面启动诊断设计

状态：已批准执行
日期：2026-07-01

## 背景

阶段 6.1 已让桌面端默认尝试托管本地 API，但当前失败时只会静默回退到离线工作台。用户看不到自己当前是离线模式、外部 API 模式还是托管 API 模式，也看不到托管启动失败的原因。

## 目标

1. 将桌面启动上下文从 Electron 主进程传给 Web 工作台。
2. 在界面头部展示当前运行模式。
3. 在诊断面板展示桌面启动诊断，包括 API URL、模式和最近一次启动失败原因。
4. 浏览器直接打开 `index.html` 时保持兼容，显示浏览器/离线模式。

## 非目标

- 不做复杂日志查看器。
- 不做系统通知、弹窗或自动重试 UI。
- 不解决 Python runtime 缺失本身，只暴露诊断结果。

## 设计

新增桌面启动上下文结构：

- `mode`: `browser-offline` / `desktop-offline` / `desktop-external-api` / `desktop-managed-api`
- `apiUrl`: 当前连接的 API URL，如有
- `managed`: 是否为桌面托管 API
- `diagnostics`: 字符串列表，用于记录成功或失败信息
- `lastError`: 最近一次启动错误文本，如有

Electron 主进程通过 `additionalArguments` 将该结构注入 renderer；preload 解析后通过 `window.moneyNeverSleep.startup` 暴露。

Web 工作台：

- 头部 `mode-pill` 改为动态文本。
- 诊断面板新增 `启动模式` 区块。
- HTTP fallback 到离线 mock 时，继续保留报告级诊断。

## 验收

1. Desktop shell 测试覆盖 startup 暴露和主进程注入结构。
2. Web workbench 测试覆盖 mode pill 和 startup 诊断入口。
3. 默认后端测试通过。
4. JS 语法检查通过，macOS `.app` 可构建。
5. 文档更新启动模式说明。