# 阶段 5.5：HTTP API 层设计规格

日期：2026-07-01
状态：已按用户批准进入设计与计划
阶段：Brainstorming 设计规格，不包含实现代码

## 1. 背景

阶段 5 已完成静态 Web 工作台，但它仍使用离线 mock 数据。后端目前提供 Python 函数入口：`analyze_stock()`、`get_analysis_report()`、`list_analysis_reports()` 和 `health()`。Web、桌面和未来移动端都需要一个稳定 HTTP 边界。

阶段 5.5 的目标是先建立最小 HTTP API 层，让客户端可以通过 JSON 请求真实调用现有分析服务。第一版不引入外部 Web 框架，先用可测试的 dispatcher 固定 API 契约，再提供标准库 HTTP server 适配器。

## 2. 设计选项

### 方案 A：直接引入 FastAPI

优点是生态成熟、类型和 OpenAPI 体验好。缺点是当前项目依赖仍为空，引入 FastAPI 会带来依赖安装、运行环境和 CI 复杂度。适合作为下一步升级。

### 方案 B：标准库 HTTP dispatcher + server 适配器

用纯 Python 实现 `HttpApiApp.handle(method, path, body)`，测试直接调用 dispatcher；运行时可用 `http.server` 启动本地 JSON API。优点是零依赖、边界清楚、测试快。缺点是没有 FastAPI 的 OpenAPI 和中间件生态。该方案推荐作为第一版。

### 方案 C：只给 Web 写本地 fetch 抽象，不做 HTTP 服务

优点是改动小。缺点是没有真实服务边界，桌面端和后续集成都无法复用。该方案不推荐。

## 3. 推荐方向

采用方案 B。第一版固定 JSON HTTP 契约：

- `GET /health`
- `POST /analysis`
- `GET /reports`
- `GET /reports/{task_id}`

`HttpApiApp` 依赖现有 `AnalysisService`，不复制业务逻辑。标准库 server 只负责 HTTP 编解码，业务测试集中在 dispatcher。

## 4. 目标

阶段 5.5 完成后，应具备：

1. 一个可测试的 HTTP dispatcher。
2. 一个标准库 `run_http_server()` 启动入口。
3. JSON 请求/响应契约。
4. Web 工作台可切换到 HTTP API service，失败时保留离线 mock fallback。
5. 文档记录 API 路由、运行方式和验证方式。

## 5. 非目标

第一版不做：

- 不引入 FastAPI 或 ASGI server。
- 不做认证、权限、CORS 配置矩阵。
- 不做异步任务队列。
- 不做 OpenAPI 自动生成。
- 不做真实 TradingAgents 长耗时轮询。

## 6. API 契约

### GET /health

响应：

```json
{"status":"ok","service":"money-never-sleep-api"}
```

### POST /analysis

请求：

```json
{"symbol":"贵州茅台","message":"请全面分析并给出投资建议"}
```

响应：`AnalysisReport.to_dict()`。

错误：缺少 symbol 或 message 时返回 400。

### GET /reports

响应：`list_analysis_reports()` 的记录数组。

支持可选 query：`limit=20`。

### GET /reports/{task_id}

响应：指定报告；不存在时返回 404。

## 7. Web 集成

`apps/web/src/app.js` 增加可切换 service 边界：

- 默认仍使用离线 mock，保证直接打开 `index.html` 可用。
- 如果 URL query 包含 `?api=<baseUrl>`，则使用 HTTP API。
- 分析请求失败时显示诊断，并回退到本地 mock 结果。

## 8. 测试策略

- dispatcher 测试：health、analysis、reports list、report detail、404、400。
- server 启动函数只做轻量 import/构造测试，不启动长期进程。
- Web 测试检查 app.js 中存在 HTTP service 边界和 fallback 逻辑。
- 全量 `services/api/tests` 回归。
- `node --check apps/web/src/app.js`。

## 9. 验收标准

1. HTTP dispatcher 能覆盖核心路由。
2. Web 工作台仍可直接打开并使用 mock。
3. Web 工作台具备 `?api=` 切换 HTTP service 的代码边界。
4. 默认测试通过。
5. 文档更新 API 路由、运行方式和下一步 FastAPI/任务队列建议。

## 10. 下一步

实现计划拆成：

1. HTTP API dispatcher。
2. 标准库 server 启动入口。
3. Web HTTP service 边界。
4. 文档、backlog、handoff 和最终验证。
