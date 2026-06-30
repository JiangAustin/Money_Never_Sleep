# 阶段 2：真实 A 股数据层设计规格

日期：2026-07-01
状态：已批准方向，待实现计划
阶段：Brainstorming 设计规格，不包含实现代码

## 1. 背景

阶段 1 已经完成单股分析后端 dry-run 闭环：股票解析、`DataContext`、Quick Agent、Mock Deep Research Engine、分析服务和 Python API 都已可测试运行。当前缺口是数据仍来自 `StaticMarketDataProvider` fixture，无法支撑真实 A 股分析。

阶段 2 的目标不是一次性接入所有真实数据源，而是先建立稳定、可测试、可诊断的数据层边界。真实数据源应服务于 Money_Never_sleep 自己的 provider 契约，而不是让业务层直接依赖任一参考项目或外部接口。

## 2. 推荐方向

采用“离线契约优先 + 一个真实行情源 smoke”的路线。

第一版先固定 provider 结果结构、fallback 语义、data gaps 和 diagnostics，再接入一个最小真实源：腾讯行情 quote provider。TradingAgents-astock 和 daily_stock_analysis 暂时作为设计参考，不直接整体迁移。

## 3. 目标

阶段 2 完成后，Money_Never_sleep 应具备：

1. 稳定的数据 provider 契约，供 `DataContextBuilder` 使用。
2. 离线 fixture provider，保证默认测试不依赖网络。
3. 腾讯行情 quote provider，用于最小真实行情 smoke。
4. provider manager 或 bundle，支持按数据类型收集 quote、technicals、fundamentals、news。
5. 显式 diagnostics，记录数据来源、是否成功、错误类型、错误消息和是否 stale。
6. data gaps 语义保持稳定：缺失数据不能静默吞掉，必须进入 `DataContext.gaps`。
7. 当前 Agent 和 API 层不需要知道数据来自静态 fixture、腾讯接口还是后续 TradingAgents adapter。

## 4. 非目标

阶段 2 第一版不做：

- 不直接接入完整 TradingAgents-astock 数据层。
- 不复制 daily_stock_analysis 的完整多市场 provider manager。
- 不做全市场选股、板块排行、资金流、龙虎榜、解禁或新闻聚合。
- 不引入数据库持久化。
- 不把网络测试设为默认必跑测试。
- 不把 provider 失败变成分析流程硬失败，除非股票标识本身无效。

## 5. 参考项目取舍

### 5.1 TradingAgents-astock

可借鉴：

- 腾讯行情字段解析，包括价格、涨跌幅、PE、PB、市值、涨跌停价。
- A 股代码到市场前缀的规则：`6/9` 为上交所，`8` 为北交所，其余为深交所。
- 后续 mootdx 名称解析和东财节流设计。

暂不直接迁移：

- mootdx TCP 客户端。
- 东财 datacenter 和 push2 复杂接口。
- 新闻、龙虎榜、解禁、资金流等宽数据面。

### 5.2 daily_stock_analysis

可借鉴：

- provider fallback 和错误摘要。
- 多市场代码规范化思路。
- run diagnostics 记录思路。

暂不直接迁移：

- 完整 DataFetcherManager。
- 多市场、多 provider、多通知链路相关复杂配置。

### 5.3 go-stock

可借鉴：

- 本地行情展示所需字段。
- 桌面端后续对实时行情、K 线和自选股的需求。

暂不直接迁移：

- Go/Wails 数据结构和数据库模型。
- Tushare 和浏览器抓取链路。

## 6. 数据层架构

阶段 2 建议形成以下层次：

```text
AnalysisService
  -> DataContextBuilder
      -> MarketDataProviderBundle
          -> QuoteProvider
          -> TechnicalsProvider
          -> FundamentalsProvider
          -> NewsProvider
          -> ProviderDiagnostics
```

### 6.1 ProviderResult

每次 provider 调用都应形成结构化结果：

- `kind`：数据类型，例如 `quote`、`technicals`、`fundamentals`、`news`。
- `source`：数据源名称，例如 `static`、`tencent`。
- `ok`：是否成功提供有效数据。
- `data`：标准化后的 dict 或 list。
- `error_type`：失败类型，成功时为空。
- `error_message`：失败说明，成功时为空。
- `fetched_at`：抓取时间，离线 fixture 可为空或固定。
- `is_stale`：是否为过期或降级数据。

### 6.2 Quote 数据结构

腾讯 quote provider 第一版标准化字段：

- `code`
- `name`
- `price`
- `last_close`
- `open`
- `high`
- `low`
- `change_pct`
- `pe_ttm`
- `pb`
- `market_cap`
- `turnover_pct`
- `limit_up`
- `limit_down`
- `source`

字段缺失时不伪造数值。无法解析的字段应省略或设为 `None`，并通过 diagnostics 说明。

### 6.3 Technicals / Fundamentals / News

阶段 2 第一版可以先保持 fixture 或空 provider：

- `technicals`：保留简单 fixture，例如 MA5/MA10/MA20；真实 K 线 provider 后续拆分。
- `fundamentals`：可从腾讯 quote 中提取 PE/PB/市值作为轻量估值摘要。
- `news`：暂时保留空 provider 或 fixture，不做真实新闻聚合。

## 7. Fallback 与 data gaps

阶段 2 的 fallback 原则：

1. provider 失败不应直接中断分析流程。
2. 失败 provider 对应的数据类型进入 `DataContext.gaps`。
3. diagnostics 必须记录失败 source、error type 和 message。
4. 如果 quote 失败但 technicals/fundamentals/news 可用，仍可返回 partial context。
5. 如果股票代码无法解析，仍由 `StockResolver` 抛出 `ValueError`。

## 8. 测试策略

默认测试必须离线、确定性、快速：

- 使用 fixture 测试 provider result 标准化。
- 使用 monkeypatch 或 fake HTTP response 测试腾讯 quote parser。
- 使用 failing provider 测试 diagnostics 和 gaps。
- 使用 provider bundle 测试 partial context。
- 真实网络 smoke 单独标记，不作为默认测试必跑项。

## 9. 验收标准

阶段 2 设计完成并进入实现后，验收标准为：

1. `services/api/tests` 默认离线测试通过。
2. `DataContextBuilder` 可以从 provider bundle 构建 context。
3. 腾讯 quote parser 可以从 fixture raw response 得到标准 quote。
4. provider 失败时，`DataContext.gaps` 和 diagnostics 都能反映失败原因。
5. `analyze_stock()` 仍可在无网络环境下通过 static provider dry run。
6. 至少提供一个可手动运行的腾讯 quote smoke 命令或测试标记，用于联网验证样例股票。

## 10. 下一步

本规格批准后，使用 writing-plans 创建阶段 2 实现计划。实现计划应优先拆成小任务：

1. provider result 和 diagnostics 契约。
2. provider bundle 与 DataContextBuilder 集成。
3. 腾讯 quote raw parser 的 fixture 测试。
4. TencentQuoteProvider 的网络调用封装。
5. static provider 和默认 API service 的兼容迁移。
6. 可选网络 smoke 和文档更新。