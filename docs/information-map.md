# 信息地图

状态：活文档
最近更新：2026-07-02

本文档是给“没有当前对话记忆的后续 agent”使用的导航页。目标是让接手者最快知道：先读哪里、每类信息在哪里、完成工作后要把哪些信息写回哪里。

## 先读顺序

如果你刚接手本仓库，请按这个顺序读取：

1. `README.md`：了解项目定位、当前实现切片、核心入口和文档规则。
2. `docs/stages.md`：确认当前阶段、已完成阶段、验证结果和下一阶段建议。
3. `docs/agent-handoff.md`：理解之前做了什么、为什么做、收益是什么、还没做什么。
4. `docs/improvement-backlog.md`：查看第一版未做事项、待改进项和优先级。
5. `docs/reference-integration-map.md`：确认三个参考项目的可借鉴能力、当前接入状态和下一步。
6. 当前阶段对应的 `docs/superpowers/specs/*.md`：理解设计思路和范围取舍。
7. 当前阶段对应的 `docs/superpowers/plans/*.md`：理解具体实现任务、测试命令和提交边界。
8. 相关代码和测试：按计划或任务触达，不要先全仓库漫游。

## 去哪里找什么

| 你要找的信息 | 首选位置 | 补充位置 |
| --- | --- | --- |
| 项目定位和默认入口 | `README.md` | `docs/agent-handoff.md` |
| 全局架构规范和新任务起手式 | `ARCHITECTURE.md` | `README.md`、`docs/agent-handoff.md` |
| 当前阶段状态 | `docs/stages.md` | `docs/agent-handoff.md` |
| 设计思路和取舍 | `docs/superpowers/specs/` | `docs/agent-handoff.md` |
| 实现步骤和测试命令 | `docs/superpowers/plans/` | commit history |
| 每次工作后的短记忆 / 决策日志 | `docs/decision-log.md` | `docs/agent-handoff.md`、`docs/stages.md` |
| 第一版没做什么 | `docs/improvement-backlog.md` | `docs/stages.md` |
| 后续推荐怎么做 | `docs/improvement-backlog.md` | `docs/agent-handoff.md` |
| 三个参考项目如何借鉴、复制和重设计 | `docs/reference-integration-map.md` | `docs/agent-handoff.md`、`docs/improvement-backlog.md` |
| 已完成阶段摘要 | `docs/agent-handoff.md` | `docs/stages.md` |
| 验证命令 | `docs/agent-handoff.md` | `docs/stages.md`、对应 plan |
| 项目本地 skills | `.github/superpowers/` | `.github/copilot-instructions.md` |
| API / 后端入口 | `services/api/money_api/main.py` | `services/api/money_api/api/v1/router.py` |
| HTTP API 边界 | `services/api/money_api/api/http.py` | `services/api/tests/test_http_api.py` |
| HTTP 任务队列、持久化、控制、超时、watchdog、可配置退避重试调度与重试观测字段 | `services/api/money_api/domains/analysis/task_queue.py` | `services/api/tests/test_http_api.py`、`services/api/tests/test_task_queue.py` |
| runtime service 装配与 auto 深度引擎默认语义 | `services/api/money_api/api/v1/router.py` | `services/api/tests/test_analysis_api.py` |
| runtime 在线 market-data bundle | `services/api/money_api/domains/market_data/ashare_runtime.py` | `services/api/tests/test_analysis_api.py`、`services/api/tests/test_agent_engine.py` |
| 工具驱动回退引擎 | `services/api/money_api/domains/analysis/tool_driven_engine.py` | `services/api/tests/test_agent_engine.py`、`services/api/tests/test_analysis_api.py` |
| 研究工具入口 | `services/api/money_api/domains/analysis/research_tools.py`、`services/api/money_api/api/http.py` | `services/api/tests/test_research_tools.py`、`services/api/tests/test_http_api.py` |
| 研究工具薄切片扩展 | `services/api/money_api/domains/analysis/research_tools.py`、`services/api/money_api/api/http.py` | `services/api/tests/test_research_tools.py`、`services/api/tests/test_http_api.py` |
| 默认 runtime 连续推进主线（5.16-5.19） | `docs/agent-handoff.md` | `docs/stages.md`、`docs/improvement-backlog.md` |
| 分析领域契约 | `services/api/money_api/domains/analysis/contracts.py` | `services/api/tests/test_analysis_contracts.py` |
| 风控纪律层 | `services/api/money_api/domains/analysis/risk_policy.py` | `services/api/tests/test_risk_policy.py` |
| 回测接口与成本参数 | `services/api/money_api/domains/analysis/backtest.py`、`services/api/money_api/domains/analysis/contracts.py` | `services/api/tests/test_backtest.py`、`services/api/tests/test_http_api.py` |
| 组合风险预算 | `services/api/money_api/domains/analysis/portfolio_risk.py` | `services/api/tests/test_portfolio_risk.py`、`services/api/tests/test_http_api.py` |
| 数据 provider 契约 | `services/api/money_api/domains/market_data/provider_results.py` | `services/api/tests/test_provider_results.py` |
| 东方财富个股新闻 provider | `services/api/money_api/domains/market_data/eastmoney_news.py` | `services/api/tests/test_eastmoney_news.py` |
| 东方财富 F10 基本面 provider | `services/api/money_api/domains/market_data/ashare_runtime.py` | `services/api/tests/test_analysis_api.py` |
| CLS 市场快讯 provider | `services/api/money_api/domains/market_data/cls_market_flash.py` | `services/api/tests/test_cls_market_flash.py` |
| 新浪公告标题 provider | `services/api/money_api/domains/market_data/sina_bulletin.py` | `services/api/tests/test_sina_bulletin.py` |
| Sina K 线 provider | `services/api/money_api/domains/market_data/sina_kline.py` | `services/api/tests/test_sina_kline.py`、`services/api/tests/test_sina_kline_smoke.py` |
| 同花顺问财可选 fundamentals provider | `services/api/money_api/domains/market_data/ashare_runtime.py` | `services/api/tests/test_analysis_api.py` |
| TradingAgents adapter 与 auto fallback 引擎 | `services/api/money_api/domains/analysis/tradingagents_engine.py` | `services/api/money_api/integrations/tradingagents_runner.py`、`services/api/tests/test_tradingagents_smoke.py` |
| 报告历史仓储 | `services/api/money_api/domains/analysis/report_repository.py` | `services/api/tests/test_report_repository.py` |
| Web 工作台、启动模式、任务控制、任务历史与重试观测展示 | `apps/web/index.html` | `apps/web/src/`、`services/api/tests/test_web_workbench.py` |
| 桌面端现状、托管 API 与启动诊断 | `apps/desktop/README.md` | `apps/desktop/package.json`、`apps/desktop/src/`、`services/api/tests/test_desktop_shell.py` |

## 做完之后写哪里

| 发生了什么 | 必须更新 |
| --- | --- |
| 阶段完成 | `docs/stages.md`、`docs/agent-handoff.md`、必要时 `README.md` |
| 改变项目定位、用户可见能力、入口命令、API、Web/Desktop 工作流或打包方式 | `README.md`、`docs/stages.md`、`docs/agent-handoff.md` |
| 每次工作后记录简短的做了什么、为什么、验证结果 | `docs/decision-log.md` |
| 第一版暂时没做、推迟功能、发现限制或技术债 | `docs/improvement-backlog.md` |
| 新增或改变设计思路 | `docs/superpowers/specs/`，并在 `docs/agent-handoff.md` 摘要 |
| 新增或改变实施步骤 | `docs/superpowers/plans/` |
| 新增验证命令、构建命令或 smoke 命令 | `docs/agent-handoff.md`、`docs/stages.md`、必要时 `README.md` |
| 新增主要代码入口或目录职责 | `README.md` 或对应子目录 README |
| 新增后续 agent 必须知道的约束 | `.github/copilot-instructions.md`、`docs/agent-handoff.md` |
| 发现可复用 workflow 或技巧 | `.github/superpowers/`；若只是项目规则则写 `.github/copilot-instructions.md` |
| 修复或完成 backlog 项 | `docs/improvement-backlog.md`，状态改为 `已完成` 并写验证依据 |
| 吸收 `go-stock`、`TradingAgents-astock` 或 `daily_stock_analysis` 的能力 | `docs/reference-integration-map.md`、`docs/decision-log.md`、必要时 `docs/stages.md` |

## 阶段收尾检查

每个阶段收尾前，后续 agent 至少检查：

1. `README.md` 是否需要同步用户可见能力。
2. `docs/stages.md` 是否更新状态、交付物、验证结果、下一阶段建议。
3. `docs/improvement-backlog.md` 是否记录本阶段没做和要改进的事项。
4. `docs/agent-handoff.md` 是否能让没有对话记忆的新 agent 理解本阶段。
5. `docs/information-map.md` 是否需要新增新的信息入口或写回位置。
6. `docs/reference-integration-map.md` 是否需要同步参考项目能力吸收状态。
7. 对应测试、构建或 smoke 命令是否已经运行并记录结果。

## 给后续 agent 的原则

- 把文档当作长期记忆，而不是把关键信息留在聊天记录里。
- 做任何第一版取舍时，写清楚“为什么现在不做”和“以后怎么做”。
- 新增能力时，留下能被验证的入口、测试命令和回滚线索。
- 如果你不确定信息该写哪里，优先写到 `docs/agent-handoff.md`，再在 `docs/improvement-backlog.md` 补待办。
- 计划和架构取舍默认使用当前可用的最新模型；执行开发和测试默认使用次一级性价比模型，除非遇到复杂调试、重大重构或高风险金融判断。
