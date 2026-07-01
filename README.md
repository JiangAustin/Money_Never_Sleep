# Money_Never_sleep

Money_Never_sleep 是一个面向 A 股智能投研的平台型工作区，目标是在自有架构边界内吸收三个参考项目的优点：

- `TradingAgents-astock`：多 Agent A 股投研流程。
- `go-stock`：桌面应用、本地数据和应用打包经验。
- `daily_stock_analysis`：Python 服务分层、API、报告、Web 和桌面边界。

当前阶段先明确 Money_Never_sleep 自己的项目边界，再按小切片吸收参考项目能力，避免直接复制或整体 fork。

English option: concise English notes can be added as a separate section or linked document when useful, while this README keeps Chinese as the default entry.

## 项目结构

```text
Money_Never_sleep/
  apps/
    web/              # Web 客户端壳
    desktop/          # 桌面客户端壳
  services/
    api/              # Python API 服务
  packages/
    shared/           # 共享契约和生成客户端
  data/
    raw/              # 原始本地输入数据
    processed/        # 派生本地数据集
    cache/            # 运行缓存，可安全重建
  docs/               # 架构、参考和路线图
  scripts/            # 本地开发脚本
```

## 第一阶段里程碑

1. 将参考项目保持为外部参考，并记录集成点。
2. 在 `services/api` 下建立最小 API 服务边界。
3. 在产品工作流更清晰后，再决定桌面壳使用 Wails、Electron 还是其他方案。
4. 只有当具体功能切片需要时，才引入真实依赖。

## 当前实现切片

第一个实现切片是“单股深度分析闭环”的后端契约：

1. 解析 A 股代码或中文股票名。
2. 构建标准化数据上下文，并显式记录数据缺口。
3. 区分快速问题和深度分析请求。
4. 通过 Agent 引擎适配器生成结构化 dry-run 报告。
5. 暴露 Python 级 API 函数，供测试和早期集成使用。

当前阶段已经完成真实 A 股数据层、TradingAgents 深度引擎边界、报告历史能力、Web 工作台第一版、JSON HTTP API 层、Electron 桌面壳，并新增风控纪律层：每份报告会附带仓位上限、止损/止盈纪律和免责声明。

阶段拆分和后续计划见 [docs/stages.md](docs/stages.md)。该文件是活文档，会随阶段完成、新想法和优先级变化持续更新。

后续 agent 的信息入口是 [docs/information-map.md](docs/information-map.md)。它说明去哪里找项目定位、设计思路、实现计划、验证命令、已知缺口，也说明完成工作后应该把新信息写回哪里。

后续改进和交接上下文集中记录在 [docs/improvement-backlog.md](docs/improvement-backlog.md) 与 [docs/agent-handoff.md](docs/agent-handoff.md)。前者记录第一版未做和待改进事项，后者帮助后续 agent 或模型理解项目演进、设计取舍、验证方式和下一步建议。

## 文档规则

- 完成阶段后，如果改变了项目定位、用户可见能力、安装/使用命令、API 入口、Web/Desktop 工作流、打包方式或重大架构方向，需要同步更新 `README.md`。
- `README.md` 默认使用中文展示。
- 需要英文说明时，提供英文选项，例如单独英文 section 或链接到英文文档，但中文仍作为默认入口。
- `docs/information-map.md` 是后续 agent 的导航页；新增重要信息入口或写回规则时必须同步更新。
- 第一版暂时未做、需要改进、未来要回来补齐的事项，统一写入 `docs/improvement-backlog.md`。
- 为方便更换 agent 或模型继续开发，阶段完成或架构变化时同步维护 `docs/agent-handoff.md`。
