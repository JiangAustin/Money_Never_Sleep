# 阶段 5.16：真实个股新闻数据接入

状态：已批准执行
日期：2026-07-01

## 背景

当前 runtime service 在 `MONEY_MARKET_DATA_MODE=tencent` 下只接入真实 quote，`news` 仍使用静态示例数据。这会限制分析上下文的时效性，也让 Web/桌面展示的新闻证据缺乏真实来源。

## 目标

1. 接入一个最小真实个股新闻 provider。
2. 保持 `ProviderResult` / `DataContextBuilder` 契约不变。
3. 在运行时服务中默认让 tencent 模式下的 `news` 走真实 provider，失败时仍保留 fallback 语义。

## 非目标

- 不在本阶段接公告、资金流、龙虎榜。
- 不引入搜索聚合层或 API key 依赖。
- 不改 TradingAgents 默认引擎选择。

## 设计

新增 `EastmoneyNewsProvider`：

- 输入：`StockIdentity`
- 输出：`ProviderResult(kind="news")`
- 数据源：东方财富 search-api
- 规范字段：
  - `title`
  - `content`
  - `time`
  - `source`
  - `url`

运行时装配：

- `QuoteOverrideProvider` 增加真实 `news_provider`
- tencent runtime 模式下：
  - quote -> 腾讯
  - news -> 东财
  - technicals/fundamentals -> 静态 fallback

失败语义：

- provider 失败时返回 `ok=False` 和空列表
- `DataContextBuilder` 继续把 `news` 记为 gap，并保留 diagnostic

## 验收

1. parser/provider 测试覆盖成功与失败路径。
2. runtime service 测试覆盖 tencent 模式下 news 来源变为 `eastmoney`。
3. API 全量测试通过。
4. 文档同步到阶段状态和 backlog。