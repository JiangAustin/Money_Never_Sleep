# 阶段 4：报告、历史与复盘设计规格

日期：2026-07-01
状态：已按用户批准进入设计与计划
阶段：Brainstorming 设计规格，不包含实现代码

## 1. 背景

阶段 1 建立了单股分析后端闭环，阶段 2 增加了真实 A 股数据层和 diagnostics，阶段 3 将 TradingAgents-astock 封装为可选深度引擎。当前仍有一个关键缺口：分析报告只保存在 `AnalysisService` 的内存字典中，进程退出后丢失，也无法列出历史分析记录。

阶段 4 的目标是在不引入重型数据库的前提下，建立可测试、可追溯、可后续替换的报告存储边界。它应保存最终报告、输入数据上下文、diagnostics 和复盘元数据，为后续 Web 工作台、报告详情页、追问和复盘奠定基础。

## 2. 设计选项

### 方案 A：继续只用内存字典

优点是代码最少。缺点是无法跨进程读取，不满足阶段 4 的核心目标。该方案只适合作为测试 fake，不适合作为阶段交付。

### 方案 B：JSON 文件仓储

每个报告保存为一个 JSON 文件，路径由 `task_id` 决定，并保留 `created_at`、股票信息、报告正文、data context snapshot 和 diagnostics。优点是零外部依赖、易读、易测试、适合当前早期阶段。缺点是查询能力有限，但可通过读取文件列表满足“最近报告”需求。该方案推荐。

### 方案 C：SQLite 仓储

优点是查询能力更强，更接近最终产品。缺点是需要更早确定表结构和迁移策略，当前报告 schema 仍在演进，过早引入数据库会增加维护成本。该方案作为阶段 5 或阶段 6 的升级方向。

## 3. 推荐方向

采用方案 B：repository 协议 + JSON 文件实现 + 内存实现。

第一版只保存单股分析报告，不做复杂筛选、分页、全文检索或追问链路。API 层新增“列出最近报告”的 Python 函数，原有 `get_analysis_report(task_id)` 继续可用。默认 API 服务可以使用本地 JSON repository；测试中使用临时目录或内存 repository。

## 4. 目标

阶段 4 完成后，Money_Never_sleep 应具备：

1. `DataContext.to_dict()` 和 `AnalysisReport.from_dict()`，让报告可序列化、可恢复。
2. `AnalysisReportRecord` 契约，记录 `task_id`、`created_at`、`stock`、`status`、`summary`、完整 `report`。
3. `AnalysisReportRepository` 协议，支持 `save(report)`、`get(task_id)`、`list_recent(limit)`。
4. `InMemoryAnalysisReportRepository`，替换当前 service 内部字典，保持测试快速。
5. `JsonFileAnalysisReportRepository`，把报告写到可配置目录。
6. `AnalysisService` 使用 repository 保存和读取报告。
7. API 层新增 `list_analysis_reports(limit=20)`。
8. 文档记录默认存储目录、验证结果和后续 SQLite/Web 升级方向。

## 5. 非目标

阶段 4 第一版不做：

- 不实现数据库迁移系统。
- 不实现 Web 页面或桌面 UI。
- 不实现全文搜索、复杂筛选、分页游标。
- 不实现报告删除、归档、标签或收藏。
- 不实现追问对话链路。
- 不把历史报告上传到远端服务。

## 6. 数据契约

### 6.1 DataContext 序列化

`DataContext.to_dict()` 应输出：

- `stock`
- `quote`
- `technicals`
- `fundamentals`
- `news`
- `gaps`
- `diagnostics`

`DataContext.from_dict(payload)` 应恢复等价对象，并对缺失字段使用空集合默认值。

### 6.2 AnalysisReport 序列化

`AnalysisReport.to_dict()` 保留现有字段，并新增完整 `data_context` 字段。现有 `data_gaps` 和 `data_diagnostics` 保留，用于兼容已有 API 消费方。

`AnalysisReport.from_dict(payload)` 应从 `data_context` 恢复完整上下文；如果旧 payload 没有 `data_context`，则使用 `stock`、`data_gaps`、`data_diagnostics` 构建最小 context。

### 6.3 AnalysisReportRecord

字段建议：

- `task_id`
- `created_at`
- `stock`
- `status`
- `summary`
- `report`

`report` 存储完整 `AnalysisReport.to_dict()`，这样历史详情不会丢失 agent views、risks、diagnostics 和 data context。

## 7. 存储策略

默认 JSON 文件路径：`data/cache/reports/<task_id>.json`。

安全规则：

1. `task_id` 只能作为文件名组件使用，不允许路径穿越。
2. 保存时创建父目录。
3. 写入使用 UTF-8 和 `ensure_ascii=False`，方便中文报告可读。
4. `list_recent(limit)` 按 `created_at` 倒序返回记录摘要。
5. JSON 文件损坏时跳过该文件，不影响其他报告读取。

## 8. API 与服务边界

`AnalysisService` 不再直接维护 `_reports` 字典，而是依赖 `AnalysisReportRepository`。

- `create_single_stock_analysis()` 生成报告后调用 `repository.save(report)`。
- `get_report(task_id)` 从 repository 读取。
- 新增 `list_reports(limit=20)` 返回 report records。

API 层：

- 保留 `analyze_stock(symbol, message)`。
- 保留 `get_analysis_report(task_id)`。
- 新增 `list_analysis_reports(limit=20)`。

默认服务使用 JSON repository；测试可直接构造 service 并注入内存 repository或临时 JSON repository。

## 9. 错误处理

1. 保存失败应让当前分析失败还是返回报告？第一版采用 fail-fast：repository 保存失败说明本地历史不可用，应暴露异常给测试和调用者。后续可改成 diagnostics 降级。
2. 读取不存在 task_id 返回 `None`。
3. 列表读取遇到损坏 JSON 文件时跳过并继续。
4. 非法 task_id 读取返回 `None`，保存时抛出 `ValueError`。

## 10. 测试策略

默认测试离线、确定性：

- DataContext / AnalysisReport round-trip 测试。
- InMemory repository 保存、读取、最近列表测试。
- JsonFile repository 保存、读取、最近列表测试。
- JsonFile repository 跳过损坏文件测试。
- AnalysisService 保存到 repository 测试。
- API `list_analysis_reports()` 测试。
- 全量 `services/api/tests` 回归。

## 11. 验收标准

阶段 4 实现完成后验收标准为：

1. `services/api/tests` 默认离线测试通过。
2. 分析报告可保存到 repository，并可用 `task_id` 恢复。
3. `list_analysis_reports(limit)` 可返回最近报告摘要。
4. 历史报告包含完整 data context、gaps、diagnostics 和 agent views。
5. 默认 API 服务具备本地 JSON 历史能力。
6. README 和 `docs/stages.md` 更新阶段 4 状态、验证结果和下一阶段建议。

## 12. 下一步

使用 writing-plans 创建阶段 4 实现计划。实现计划应拆成小任务：

1. DataContext / AnalysisReport round-trip 契约。
2. report repository 契约与内存实现。
3. JSON 文件 repository。
4. AnalysisService repository 集成。
5. API history 查询函数。
6. 文档与最终验证。
