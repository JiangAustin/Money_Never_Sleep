# Money_Never_sleep Desktop

Desktop client shell for Money_Never_sleep.

当前第一版选择 Electron：直接承载 `apps/web/index.html`，并通过 `extraResources` 在打包后携带 Web 工作台静态资源。

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

构建 macOS `.app`：

```bash
cd apps/desktop
npm run build:mac
```

构建产物：`apps/desktop/dist/mac-arm64/Money Never Sleep.app`。

## HTTP API 模式

默认桌面壳打开离线 Web 工作台。如需连接本地 HTTP API：

```bash
MNS_DESKTOP_API_URL=http://127.0.0.1:8000 npm start
```

打包后的应用同样读取 `MNS_DESKTOP_API_URL`，并把它传给 Web 工作台的 `?api=` 模式。

## 当前边界

- 不内嵌 Python API server。
- 不做签名、公证、DMG、自动更新。
- 未设置自定义应用图标。
- Electron 依赖已通过 `npm audit --audit-level=high` 检查。
