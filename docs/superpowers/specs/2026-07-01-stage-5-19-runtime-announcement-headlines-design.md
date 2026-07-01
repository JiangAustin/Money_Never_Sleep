# 阶段 5.19：runtime 公司公告标题流接入

状态：已批准执行
日期：2026-07-01

## 背景

阶段 5.18 已让 runtime `news` 同时覆盖个股新闻与市场快讯，但仍缺少更接近公司事件面的公告标题流。当前上下文能看到资讯与情绪，却不容易直接捕捉正式公告、业绩快报、担保、减持、投资者关系记录等公司事件。

## 目标

1. 接入一个最小的公司公告标题 provider。
2. 不扩展 `DataContext` schema，继续并入现有 `news` 列表。
3. 默认 runtime 模式下让 `news` 同时包含：
   - 东方财富个股新闻
   - CLS 市场快讯
   - 公司公告标题

## 非目标

- 不抓公告正文全文。
- 不引入 cninfo/SSE/SZSE 多源聚合。
- 不做公告事件分类或相关性排序。

## 设计

新增 `SinaBulletinProvider`：

- 源：新浪财经个股公告列表页
- 输出统一字段：
  - `title`
  - `content`，默认空字符串
  - `time`
  - `source`
  - `url`

组合策略：

- 在 `CompositeNewsProvider` 中把 `SinaBulletinProvider` 作为第三个 source
- 按标题去重，保留顺序：个股新闻 -> 市场快讯 -> 公告标题

## 验收

1. parser/provider 测试覆盖成功与失败路径。
2. runtime service 测试覆盖默认 `news` 里出现公告来源。
3. API 全量测试通过。