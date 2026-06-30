# 阶段 6：桌面端与本地体验设计规格

日期：2026-07-01
状态：已按用户批准进入设计与计划
阶段：Brainstorming 设计规格，不包含实现代码

## 1. 背景

阶段 5 已完成静态 Web 工作台，阶段 5.5 已补齐 JSON HTTP API 层。当前 `apps/desktop/` 仍是预留目录，没有 macOS 构建入口。用户偏好是在完成阶段后尽量构建新的 macOS 版本，因此阶段 6 的首要目标是建立最小可构建桌面壳。

## 2. 选型比较

### Electron

优点：与现有静态 Web 工作台天然兼容；Node/npm 已可用；macOS `.app` 构建路径成熟；第一版最快落地。缺点：体积较大，后续需要治理自动更新和资源打包。

### Tauri

优点：体积小，系统 WebView，长期桌面体验更轻。缺点：需要 Rust/Tauri 工具链，当前仓库没有相关配置；第一版构建不如 Electron 直接。

### Wails

优点：go-stock 参考项目使用 Go/Wails，有桌面经验可借鉴。缺点：Money_Never_sleep 当前主轴是 Python API + Web，Wails 会引入 Go 主体边界，不适合作为第一版壳。

## 3. 推荐方向

第一版选择 Electron。目标不是一次性做完整桌面产品，而是把现有 Web 工作台包装成可构建的 macOS 应用，并为后续接本地 HTTP API、托盘、通知和自动更新保留边界。

## 4. 目标

阶段 6 完成后应具备：

1. `apps/desktop/package.json`，定义 Electron start 和 macOS build 脚本。
2. `apps/desktop/src/main.js`，创建 BrowserWindow 并加载 `apps/web/index.html`。
3. `apps/desktop/src/preload.js`，保留安全 preload 边界。
4. Electron build 配置，使用 `extraResources` 打包 Web 静态资源。
5. pytest 结构测试，确认桌面入口、脚本和 Web 资源加载策略。
6. `npm install` 生成 lockfile，`npm run build:mac` 生成 macOS `.app`。
7. README、stages、handoff、backlog、information-map 更新桌面入口和验证命令。

## 5. 非目标

第一版不做：

- 不做自动更新。
- 不做托盘、菜单、系统通知。
- 不做签名、公证和 DMG 安装包。
- 不内嵌 Python API server 进程。
- 不做登录、权限或本地密钥管理。

## 6. 桌面加载策略

开发和构建都以 Web 工作台为第一屏：

- 开发时加载仓库内 `apps/web/index.html`。
- 打包后加载 `process.resourcesPath/web/index.html`。
- 如果环境变量 `MNS_DESKTOP_API_URL` 存在，向 Web 传入 `?api=<url>`，让 Web 走 HTTP API 模式。
- 默认不启动 API server，保持桌面壳简单可构建。

## 7. 测试策略

- Python pytest 检查 `package.json` scripts/build 配置。
- Python pytest 检查 `main.js` 加载 Web 工作台和 `MNS_DESKTOP_API_URL`。
- `node --check apps/desktop/src/main.js apps/desktop/src/preload.js`。
- `cd apps/desktop && npm install && npm run build:mac`。
- 后端全量测试继续通过。

## 8. 验收标准

1. `apps/desktop` 有可运行 Electron 桌面壳。
2. `npm run build:mac` 能生成 macOS `.app` 目录。
3. Web 工作台被打包为 extra resources。
4. 默认测试和 JS 语法检查通过。
5. 文档记录如何启动、如何构建、构建产物位置和暂缓事项。

## 9. 下一步

实现计划拆成：

1. 桌面 package 和结构测试。
2. Electron main/preload 壳。
3. npm install 与 macOS build 验证。
4. 文档、backlog、handoff 和最终收尾。
