# 信息地图

状态：活文档
最近更新：2026-07-01

本文档是给“没有当前对话记忆的后续 agent”使用的导航页。目标是让接手者最快知道：先读哪里、每类信息在哪里、完成工作后要把哪些信息写回哪里。

## 先读顺序

如果你刚接手本仓库，请按这个顺序读取：

1. `README.md`：了解项目定位、当前实现切片、核心入口和文档规则。
2. `docs/stages.md`：确认当前阶段、已完成阶段、验证结果和下一阶段建议。
3. `docs/agent-handoff.md`：理解之前做了什么、为什么做、收益是什么、还没做什么。
4. `docs/improvement-backlog.md`：查看第一版未做事项、待改进项和优先级。
5. 当前阶段对应的 `docs/superpowers/specs/*.md`：理解设计思路和范围取舍。
6. 当前阶段对应的 `docs/superpowers/plans/*.md`：理解具体实现任务、测试命令和提交边界。
7. 相关代码和测试：按计划或任务触达，不要先全仓库漫游。

## 去哪里找什么

| 你要找的信息 | 首选位置 | 补充位置 |
| --- | --- | --- |
| 项目定位和默认入口 | `README.md` | `docs/agent-handoff.md` |
| 当前阶段状态 | `docs/stages.md` | `docs/agent-handoff.md` |
| 设计思路和取舍 | `docs/superpowers/specs/` | `docs/agent-handoff.md` |
| 实现步骤和测试命令 | `docs/superpowers/plans/` | commit history |
| 第一版没做什么 | `docs/improvement-backlog.md` | `docs/stages.md` |
| 后续推荐怎么做 | `docs/improvement-backlog.md` | `docs/agent-handoff.md` |
| 已完成阶段摘要 | `docs/agent-handoff.md` | `docs/stages.md` |
| 验证命令 | `docs/agent-handoff.md` | `docs/stages.md`、对应 plan |
| 项目本地 skills | `.github/superpowers/` | `.github/copilot-instructions.md` |
| API / 后端入口 | `services/api/money_api/main.py` | `services/api/money_api/api/v1/router.py` |
| HTTP API 边界 | `services/api/money_api/api/http.py` | `services/api/tests/test_http_api.py` |
| runtime service 装配 | `services/api/money_api/api/v1/router.py` | `services/api/tests/test_analysis_api.py` |
| 分析领域契约 | `services/api/money_api/domains/analysis/contracts.py` | `services/api/tests/test_analysis_contracts.py` |
| 风控纪律层 | `services/api/money_api/domains/analysis/risk_policy.py` | `services/api/tests/test_risk_policy.py` |
| 回测接口与成本参数 | `services/api/money_api/domains/analysis/backtest.py`、`services/api/money_api/domains/analysis/contracts.py` | `services/api/tests/test_backtest.py`、`services/api/tests/test_http_api.py` |
| 组合风险预算 | `services/api/money_api/domains/analysis/portfolio_risk.py` | `services/api/tests/test_portfolio_risk.py`、`services/api/tests/test_http_api.py` |
| 数据 provider 契约 | `services/api/money_api/domains/market_data/provider_results.py` | `services/api/tests/test_provider_results.py` |
| Sina K 线 provider | `services/api/money_api/domains/market_data/sina_kline.py` | `services/api/tests/test_sina_kline.py`、`services/api/tests/test_sina_kline_smoke.py` |
| TradingAgents adapter | `services/api/money_api/domains/analysis/tradingagents_engine.py` | `services/api/money_api/integrations/tradingagents_runner.py` |
| 报告历史仓储 | `services/api/money_api/domains/analysis/report_repository.py` | `services/api/tests/test_report_repository.py` |
| Web 工作台 | `apps/web/index.html` | `apps/web/src/`、`services/api/tests/test_web_workbench.py` |
| 桌面端现状与托管 API | `apps/desktop/README.md` | `apps/desktop/package.json`、`apps/desktop/src/`、`services/api/tests/test_desktop_shell.py` |

## 做完之后写哪里

| 发生了什么 | 必须更新 |
| --- | --- |
| 阶段完成 | `docs/stages.md`、`docs/agent-handoff.md`、必要时 `README.md` |
| 改变项目定位、用户可见能力、入口命令、API、Web/Desktop 工作流或打包方式 | `README.md`、`docs/stages.md`、`docs/agent-handoff.md` |
| 第一版暂时没做、推迟功能、发现限制或技术债 | `docs/improvement-backlog.md` |
| 新增或改变设计思路 | `docs/superpowers/specs/`，并在 `docs/agent-handoff.md` 摘要 |
| 新增或改变实施步骤 | `docs/superpowers/plans/` |
| 新增验证命令、构建命令或 smoke 命令 | `docs/agent-handoff.md`、`docs/stages.md`、必要时 `README.md` |
| 新增主要代码入口或目录职责 | `README.md` 或对应子目录 README |
| 新增后续 agent 必须知道的约束 | `.github/copilot-instructions.md`、`docs/agent-handoff.md` |
| 发现可复用 workflow 或技巧 | `.github/superpowers/`；若只是项目规则则写 `.github/copilot-instructions.md` |
| 修复或完成 backlog 项 | `docs/improvement-backlog.md`，状态改为 `已完成` 并写验证依据 |

## 阶段收尾检查

每个阶段收尾前，后续 agent 至少检查：

1. `README.md` 是否需要同步用户可见能力。
2. `docs/stages.md` 是否更新状态、交付物、验证结果、下一阶段建议。
3. `docs/improvement-backlog.md` 是否记录本阶段没做和要改进的事项。
4. `docs/agent-handoff.md` 是否能让没有对话记忆的新 agent 理解本阶段。
5. `docs/information-map.md` 是否需要新增新的信息入口或写回位置。
6. 对应测试、构建或 smoke 命令是否已经运行并记录结果。

## 给后续 agent 的原则

- 把文档当作长期记忆，而不是把关键信息留在聊天记录里。
- 做任何第一版取舍时，写清楚“为什么现在不做”和“以后怎么做”。
- 新增能力时，留下能被验证的入口、测试命令和回滚线索。
- 如果你不确定信息该写哪里，优先写到 `docs/agent-handoff.md`，再在 `docs/improvement-backlog.md` 补待办。
