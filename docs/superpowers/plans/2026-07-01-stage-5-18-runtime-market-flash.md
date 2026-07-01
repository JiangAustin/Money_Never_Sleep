# 阶段 5.18：runtime 市场快讯接入计划

状态：已完成
日期：2026-07-01

## 任务 1：测试先行

新增或扩展：

- `services/api/tests/test_cls_market_flash.py`
- `services/api/tests/test_eastmoney_news.py`
- `services/api/tests/test_analysis_api.py`

覆盖：

- CLS 快讯解析与错误路径
- 组合 news provider 合并结果
- runtime 模式下默认 news 列表包含 CLS 快讯

## 任务 2：实现

更新：

- `services/api/money_api/domains/market_data/cls_market_flash.py`
- `services/api/money_api/domains/market_data/eastmoney_news.py`
- `services/api/money_api/api/v1/router.py`

## 任务 3：验证与收尾

- 运行 API 测试、provider 测试、Python 编译检查、Node 语法检查、macOS 构建
- 更新阶段文档、backlog、handoff、README
- 合并、推送、清理