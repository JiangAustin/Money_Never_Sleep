# 阶段 5.18：runtime 市场快讯接入

状态：已批准执行
日期：2026-07-01

## 背景

阶段 5.16 已接入真实个股新闻，但分析上下文仍缺少更广的市场层资讯。当前 `DataContext.news` 只承载个股新闻，对政策、情绪和突发事件的覆盖不足。

## 目标

1. 在不扩展 schema 的前提下，把市场快讯并入现有 `news` 列表。
2. 默认 runtime 模式下同时提供：
   - 东方财富个股新闻
   - 财联社市场快讯
3. 保持 `ProviderResult(kind="news")` 与 `DataContextBuilder` 契约不变。

## 非目标

- 不新增单独的 `global_news` 或 `announcements` 字段。
- 不做相关性排序、摘要增强或去重策略复杂化。
- 不在本阶段接交易所公告源。

## 设计

新增 `ClsMarketFlashProvider`：

- 读取 `https://www.cls.cn/nodeapi/telegraphList`
- 规范字段：
  - `title`
  - `content`
  - `time`
  - `source`
  - `url`（允许为空）

新增 `CompositeNewsProvider`：

- 聚合 `EastmoneyNewsProvider` 和 `ClsMarketFlashProvider`
- 按顺序拼接，再按 `title` 去重
- 任一源失败不应拖垮整体；只要有一方成功即 `ok=True`
- `source` 标记使用组合名，例如 `eastmoney+cls`

runtime 装配：

- tencent 模式下 `news_provider` 改为组合 provider

## 验收

1. provider 测试覆盖 CLS 解析、失败语义和组合行为。
2. runtime service 测试覆盖默认新闻流里同时出现个股新闻和 CLS 快讯。
3. API 全量测试通过。