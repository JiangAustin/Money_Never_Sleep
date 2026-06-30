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
- `docs/information-map.md` 是后续 agent 的信息地图；它必须说明去哪里找什么，以及完成工作后去哪里留下什么信息。
- 所有第一版暂时没做、需要改进、后续必须回来补齐的事项，统一记录到 `docs/improvement-backlog.md`，不要只留在对话或 commit message 中。
- 每完成阶段、改变架构方向或留下重要限制时，同步更新 `docs/agent-handoff.md`，让后续 agent 能理解之前做了什么、为什么做、收益是什么、还没做什么、下一步建议怎么做。

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
| 2. 真实 A 股数据层 | 已完成 | 用真实 provider 替换当前离线 fixture，并保留 fallback 和数据缺口语义 | ProviderResult 契约、DataContext diagnostics、腾讯 quote parser/provider、可选 network smoke | 离线测试通过，至少一个真实样例可手动验证 |
| 3. TradingAgents 深度引擎接入 | 已完成 | 将 TradingAgents-astock 作为 DeepResearchEngine 的真实实现接入 | TradingAgents adapter、runner 协议、真实 runner 壳、配置入口、可选 smoke | mock 与真实引擎可切换，失败时可返回 failed report |
| 4. 报告、历史与复盘 | 已完成 | 保存报告和分析上下文，支持历史查询、复盘和追问 | 报告 round-trip 契约、repository、JSON 持久化、历史查询 API | 报告可重复读取，关键证据和 data gaps 可追溯 |
| 5. Web 工作台 | 已完成 | 提供用户可操作的单股分析入口和报告阅读体验 | 静态 Web 工作台、离线 mock 分析、最近报告、报告详情、数据诊断 | 用户可从 Web 发起 mock 分析并查看结构化报告 |
| 6. 桌面端与本地体验 | 待决策 | 决定 Electron、Tauri 或 Wails，并提供本地应用体验 | 桌面壳、配置管理、本地缓存、打包脚本 | macOS 版本可构建并能访问核心分析能力 |
| 7. 风控、回测与组合 | 待计划 | 从单股建议扩展到纪律、验证和组合层面 | 风控规则、回测接口、组合视图、绩效归因 | 建议可被复盘验证，不只输出买卖结论 |

## 当前阶段结论

阶段 5 已完成。当前系统已具备第一版 Web 工作台：

1. `apps/web/index.html` 可直接打开，无需 Node 依赖或构建步骤。
2. 页面支持输入股票和问题，生成离线 mock 分析报告。
3. 页面支持查看最近报告列表并切换报告详情。
4. 报告详情展示 summary、reasons、risks、agent views、data gaps、diagnostics 和 data context。
5. Web mock 数据字段与后端 `AnalysisReport.to_dict()` 保持兼容。
6. Web README 记录静态打开方式和后续 HTTP API 接入方向。

离线验证命令：

```bash
PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -v
```

离线结果：`59 passed, 2 skipped`。

Web 打开方式：`apps/web/index.html`。

## 下一阶段建议

建议进入阶段 6“桌面端与本地体验”。下一步先确定 Electron、Tauri 或 Wails，然后把 Web 工作台作为桌面壳的第一屏，补齐 macOS 构建入口。

## 想法池

- 把 TradingAgents-astock 接成 `DeepResearchEngine` 的真实实现。
- 借鉴 daily_stock_analysis 的数据源 fallback 和报告管理。
- 借鉴 go-stock 的行情图表、桌面体验和工具分组。
- 为每次分析保存输入数据摘要，便于后续复盘和对比。
- 后续 README 可增加英文文档链接，例如 `docs/README_EN.md`。
