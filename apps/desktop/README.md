# Money_Never_sleep Desktop

Desktop client shell for Money_Never_sleep.

当前第一版选择 Electron：直接承载 `apps/web/index.html`，并通过 `extraResources` 在打包后携带 Web 工作台静态资源和 `services/api` 源码资源。

## 命令

安装依赖：

```bash
cd apps/desktop
npm install
```

本地启动：

```bash
cd apps/desktop
npm start
```

默认行为：若未设置 `MNS_DESKTOP_API_URL`，桌面端会尝试自动拉起本地 Python API server，并在健康检查成功后以 `?api=` 模式加载 Web 工作台。

工作台头部和诊断面板会显示当前启动模式：

- `桌面托管 API`：本地 server 已成功启动。
- `桌面外部 API`：使用 `MNS_DESKTOP_API_URL` 指向的服务。
- `桌面离线模式`：托管启动失败，已回退到离线工作台。
- `浏览器离线模式`：直接打开 `index.html`，不带桌面启动上下文。

构建 macOS `.app`：

```bash
cd apps/desktop
npm run build:mac
```

构建产物：`apps/desktop/dist/mac-arm64/Money Never Sleep.app`。

## HTTP API 模式

如需连接外部或手动启动的本地 HTTP API：

```bash
MNS_DESKTOP_API_URL=http://127.0.0.1:8000 npm start
```

打包后的应用同样读取 `MNS_DESKTOP_API_URL`，并把它传给 Web 工作台的 `?api=` 模式。

如需指定桌面托管 server 使用的 Python：

```bash
MNS_DESKTOP_PYTHON_BIN=/path/to/python3 npm start
```

桌面托管 server 默认使用：

- `MONEY_MARKET_DATA_MODE=tencent`
- `MONEY_DEEP_ENGINE=mock`

如需尝试真实 TradingAgents，可显式设置：

```bash
MONEY_DEEP_ENGINE=tradingagents npm start
```

## 当前边界

- 桌面会托管本地 Python API server，但仍依赖本机已有 Python；当前不随应用打包 Python runtime。
- 启动失败原因目前以工作台诊断信息展示，不提供独立日志窗口或重试按钮。
- 不做签名、公证、DMG、自动更新。
- 未设置自定义应用图标。
- Electron 依赖已通过 `npm audit --audit-level=high` 检查。
