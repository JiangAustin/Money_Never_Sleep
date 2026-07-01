# 阶段 5.19：runtime 公司公告标题流接入计划

状态：执行中
日期：2026-07-01

## 任务 1：测试先行

新增或扩展：

- `services/api/tests/test_sina_bulletin.py`
- `services/api/tests/test_analysis_api.py`

覆盖：

- 公告列表 parser 能解析标题、时间、链接
- provider 失败时返回标准化错误
- runtime 默认 `news` 同时包含公告来源

## 任务 2：实现

更新：

- `services/api/money_api/domains/market_data/sina_bulletin.py`
- `services/api/money_api/domains/market_data/eastmoney_news.py`
- `services/api/money_api/api/v1/router.py`

## 任务 3：验证与收尾

- 运行 API 测试、provider 测试、Python 编译检查、Node 语法检查、macOS 构建
- 更新阶段文档、backlog、handoff、README
- 合并、推送、清理