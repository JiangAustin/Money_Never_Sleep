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

当前阶段已经完成真实 A 股数据层，并接入 TradingAgents 深度引擎边界：默认 API 仍保持 mock deep engine，TradingAgents-astock 通过可选 adapter/runner 成为显式启用的真实深度投研后端。

阶段拆分和后续计划见 [docs/stages.md](docs/stages.md)。该文件是活文档，会随阶段完成、新想法和优先级变化持续更新。

## 文档规则

- 完成阶段后，如果改变了项目定位、用户可见能力、安装/使用命令、API 入口、Web/Desktop 工作流、打包方式或重大架构方向，需要同步更新 `README.md`。
- `README.md` 默认使用中文展示。
- 需要英文说明时，提供英文选项，例如单独英文 section 或链接到英文文档，但中文仍作为默认入口。
