# 阶段路线图

状态：活文档
最近更新：2026-07-01

本文档用于记录 Money_Never_sleep 每个阶段要完成什么、验收标准、当前状态和后续想法。后续有新的判断、优先级变化或产品想法时，优先更新本文档，再进入实现计划。

## 更新规则

- 每完成一个阶段，更新对应阶段的状态、交付物、验证结果和下一步建议。
- 当新增想法影响阶段范围、顺序或验收标准时，先更新本文档，再拆分实现计划。
- 当阶段改变项目定位、用户可见能力、安装/使用命令、API 入口、Web/Desktop 工作流、打包方式或重大架构方向时，同步更新 `README.md`。
- README 默认使用中文；需要英文时提供英文 section 或英文文档链接。
- 可以主动调用任何对当前目标有帮助的 skills，例如在进入阶段 2“真实 A 股数据层”前，先使用 brainstorming 完成设计规格，再使用 writing-plans 形成实现计划；仍需遵守各 skill 的用户批准关卡和仓库安全规则。

## 状态说明

- `已完成`：代码、文档、验证和提交已完成。
- `进行中`：正在实现或正在审查。
- `待计划`：方向明确，但尚未形成实现计划。
- `待决策`：需要先做技术或产品取舍。

## 阶段总览

| 阶段 | 状态 | 目标 | 主要交付物 | 验收标准 |
| --- | --- | --- | --- | --- |
| 0. 项目边界与设计 | 已完成 | 明确 Money_Never_sleep 不直接 fork 参考项目，而是自建平台骨架 | 设计规格、实现计划、README 初始说明 | 设计文档和实现计划已提交 |
| 1. 单股分析后端契约 | 已完成 | 建立可测试的单股深度分析 dry-run 后端闭环 | 领域契约、股票解析、数据上下文、Agent 适配器、分析服务、Python API | `services/api/tests` 全部通过 |
| 2. 真实 A 股数据层 | 待计划 | 用真实 provider 替换当前离线 fixture，并保留 fallback 和数据缺口语义 | 数据 provider 接口、A 股行情/基础信息 adapter、缓存策略、错误诊断 | 离线测试通过，至少一个真实样例可手动验证 |
| 3. TradingAgents 深度引擎接入 | 待计划 | 将 TradingAgents-astock 作为 DeepResearchEngine 的真实实现接入 | 引擎适配器、配置入口、超时/成本控制、失败降级 | mock 与真实引擎可切换，失败时可返回 partial report |
| 4. 报告、历史与复盘 | 待计划 | 保存报告和分析上下文，支持历史查询、复盘和追问 | 报告 schema、存储层、历史查询 API、复盘元数据 | 报告可重复读取，关键证据和 data gaps 可追溯 |
| 5. Web 工作台 | 待计划 | 提供用户可操作的单股分析入口和报告阅读体验 | Web 页面、任务状态、报告详情、追问入口 | 用户可从 Web 发起分析并查看结构化报告 |
| 6. 桌面端与本地体验 | 待决策 | 决定 Electron、Tauri 或 Wails，并提供本地应用体验 | 桌面壳、配置管理、本地缓存、打包脚本 | macOS 版本可构建并能访问核心分析能力 |
| 7. 风控、回测与组合 | 待计划 | 从单股建议扩展到纪律、验证和组合层面 | 风控规则、回测接口、组合视图、绩效归因 | 建议可被复盘验证，不只输出买卖结论 |

## 当前阶段结论

阶段 1 已完成。当前系统已经具备一个无网络依赖的后端 dry-run 闭环：

1. 解析 A 股代码或中文名称。
2. 构建标准化 `DataContext`，显式记录数据缺口。
3. 用 `QuickAgentRouter` 区分快速问题和深度分析请求。
4. 用 `MockDeepResearchEngine` 生成符合契约的结构化报告。
5. 通过 Python 级 API 暴露 `analyze_stock()` 和 `get_analysis_report()`。

最终验证：

```bash
PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -v
```

结果：`25 passed`。

## 下一阶段建议

建议下一阶段先做“真实 A 股数据层”，而不是直接接 TradingAgents-astock。

原因：

- 深度 Agent 的质量取决于稳定、可解释、可追溯的数据上下文。
- 当前 mock engine 已经固定了 Agent 接口，下一步最缺的是真实数据输入。
- 先把数据 provider、fallback、缓存和 data gaps 做扎实，后续接 TradingAgents 时更容易定位问题。

阶段 2 建议拆成独立设计和实现计划，先覆盖最小数据集：

1. A 股代码与名称解析增强。
2. 实时行情或最近行情。
3. 日线 K 线和基础技术指标。
4. 基础财务/估值摘要。
5. 新闻或公告占位 provider。
6. provider 失败时的 data gaps 和诊断信息。

阶段 2 执行前流程：

1. 使用 brainstorming 梳理真实 A 股数据层的目标、范围、数据源优先级、fallback 语义和验收标准。
2. 形成并提交阶段 2 设计规格。
3. 使用 writing-plans 拆分阶段 2 的实现任务。
4. 用户批准计划后，再进入实现。

## 想法池

- 把 TradingAgents-astock 接成 `DeepResearchEngine` 的真实实现。
- 借鉴 daily_stock_analysis 的数据源 fallback 和报告管理。
- 借鉴 go-stock 的行情图表、桌面体验和工具分组。
- 为每次分析保存输入数据摘要，便于后续复盘和对比。
- 后续 README 可增加英文文档链接，例如 `docs/README_EN.md`。