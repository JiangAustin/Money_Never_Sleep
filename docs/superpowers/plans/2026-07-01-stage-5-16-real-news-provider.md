# 阶段 5.16：真实个股新闻数据接入计划

状态：执行中
日期：2026-07-01

## 任务 1：测试先行

新增或扩展：

- `services/api/tests/test_eastmoney_news.py`
- `services/api/tests/test_analysis_api.py`

覆盖：

- 新闻 parser 能解析东财返回
- provider 失败时返回标准化错误
- runtime service 在 tencent 模式下使用真实 news provider

## 任务 2：实现

更新：

- `services/api/money_api/domains/market_data/eastmoney_news.py`
- `services/api/money_api/api/v1/router.py`

## 任务 3：验证与收尾

- 运行 API 测试与新增 provider 测试
- 运行 Node 语法检查与 macOS 构建
- 更新 `docs/stages.md`、`docs/improvement-backlog.md`、`docs/agent-handoff.md`、`docs/information-map.md`、`README.md`
- 合并、推送、清理