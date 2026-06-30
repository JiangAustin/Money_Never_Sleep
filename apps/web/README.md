# Money_Never_sleep Web

当前 Web 工作台是零依赖静态版本，可直接打开 `apps/web/index.html`。

第一版使用离线 mock 数据模拟后端 `AnalysisReport` 契约，支持本地发起分析、查看最近报告和报告详情。后续接入 HTTP API 时，优先替换 `src/app.js` 中的本地 service 边界。

## 当前边界

- 不需要 Node 依赖或构建步骤。
- 不直接调用真实后端，只展示契约一致的离线 mock 工作流。
- 页面入口为 `index.html`，样式和交互逻辑分别位于 `src/styles.css` 与 `src/app.js`。

## 后续方向

- 增加 HTTP API 适配层。
- 将最近报告列表替换为后端 `list_analysis_reports()` 对应接口。
- 将本地 mock 分析替换为真实任务创建和报告轮询。
