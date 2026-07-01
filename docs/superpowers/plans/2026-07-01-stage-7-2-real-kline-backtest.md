# 阶段 7.2 真实 K 线回测数据源实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 让回测接口能通过 Sina 日线 K 线 provider 自动获取价格序列。

**架构：** 新增 `SinaKLineProvider` 负责真实/注入式 K 线数据获取，返回 `ProviderResult(kind="price_series")`；`AnalysisService` 增加 provider 回测方法；Python/HTTP API 支持 `source=sina`。

**技术栈：** Python 标准库、dataclasses、pytest、现有 ProviderResult 和 BacktestResult 契约。

---

## 任务 1：Sina K 线 parser/provider

**文件：**

- 创建：`services/api/money_api/domains/market_data/sina_kline.py`
- 创建：`services/api/tests/test_sina_kline.py`

实现 fixture parser、market symbol、provider success/failure。

## 任务 2：Service 和 API 接入 provider 回测

**文件：**

- 修改：`services/api/money_api/domains/analysis/service.py`
- 修改：`services/api/money_api/api/v1/router.py`
- 修改：`services/api/money_api/main.py`
- 修改：`services/api/money_api/api/http.py`
- 修改：`services/api/tests/test_analysis_api.py`
- 修改：`services/api/tests/test_http_api.py`

实现 `backtest_report_with_price_provider()`，HTTP body 支持 `source=sina` 和 `limit`。

## 任务 3：文档和最终验证

**文件：**

- 修改：`README.md`
- 修改：`docs/stages.md`
- 修改：`docs/improvement-backlog.md`
- 修改：`docs/agent-handoff.md`
- 修改：`docs/information-map.md`

记录阶段 7.2 完成、真实网络 smoke 暂缓、验证结果和下一步建议。

## 自检结果

- 默认测试不访问网络。
- 真实 K 线只作为 provider 能力接入，不引入缓存和复权。
- 回测仍沿用现有 `SimpleBacktestEngine`。
