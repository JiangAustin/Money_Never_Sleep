# 阶段 7.2：真实 K 线回测数据源设计规格

日期：2026-07-01
状态：已按用户指令继续执行
阶段：设计规格，不包含实现代码

## 1. 背景

阶段 7.1 已经完成确定性回测接口，但调用方必须手工传入价格序列。下一步要让回测能从真实行情 provider 获取日线价格，减少手工输入，让回测接口更接近真实使用。

## 2. 推荐方向

第一版新增 Sina 日线 K 线 provider。原因是它是 HTTP JSON 风格接口，可通过标准库访问，且可以用注入式 transport 做离线测试。默认测试不访问网络，真实网络验证后续用 opt-in smoke。

## 3. 目标

1. 新增 `SinaKLineProvider`，返回 `ProviderResult(kind="price_series")`。
2. 新增 `parse_sina_kline_payload()`，把原始 payload 转成 `BacktestPricePoint`。
3. `AnalysisService` 支持从 provider 获取价格序列并回测。
4. Python API 和 HTTP API 支持 `{ "source": "sina", "limit": 60 }`。
5. 默认测试离线、确定性。
6. 文档记录真实网络 smoke 后续仍待执行。

## 4. 非目标

- 不做复权。
- 不做分钟线。
- 不做多 provider fallback。
- 不做缓存。
- 不把网络 smoke 纳入默认测试。

## 5. 验收标准

1. Sina parser fixture 测试通过。
2. Provider 成功/失败返回结构化 diagnostics。
3. 回测 API 能用 provider 返回的 price series。
4. 全量测试、JS 检查、macOS 构建通过。
