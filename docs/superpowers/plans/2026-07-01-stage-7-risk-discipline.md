# 阶段 7 风控纪律层实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 为所有分析报告增加确定性的风险控制计划，让建议带有仓位上限、止损/止盈纪律、数据缺口降级和免责声明。

**架构：** 在分析契约中新增 `RiskControlRule` / `RiskControlPlan`，新增 `DefaultRiskPolicy` 负责从 `AnalysisReport` 生成计划，`AnalysisService` 在保存报告前应用策略。

**技术栈：** Python dataclasses、Protocol/普通类、pytest、现有 `services/api/money_api` 包结构。

---

## 文件结构

- 修改：`services/api/money_api/domains/analysis/contracts.py`
- 创建：`services/api/money_api/domains/analysis/risk_policy.py`
- 修改：`services/api/money_api/domains/analysis/service.py`
- 修改：`services/api/tests/test_analysis_contracts.py`
- 创建：`services/api/tests/test_risk_policy.py`
- 修改：`services/api/tests/test_analysis_service.py`
- 修改：`services/api/tests/test_analysis_api.py`
- 修改：`apps/web/src/mockData.js`
- 修改：`services/api/tests/test_web_workbench.py`
- 修改：`README.md`、`docs/stages.md`、`docs/improvement-backlog.md`、`docs/agent-handoff.md`、`docs/information-map.md`

---

### 任务 1：风控契约

**文件：**

- 修改：`services/api/money_api/domains/analysis/contracts.py`
- 修改：`services/api/tests/test_analysis_contracts.py`

- [ ] **步骤 1：编写失败测试**

追加测试：

```python
def test_risk_control_plan_round_trip() -> None:
    plan = RiskControlPlan(
        max_position_pct=0.1,
        stop_loss_pct=0.08,
        take_profit_pct=0.15,
        time_horizon="5-20 个交易日",
        rules=[RiskControlRule(name="confidence", level="medium", message="中等置信度")],
        disclaimer="非投资建议",
    )

    assert RiskControlPlan.from_dict(plan.to_dict()) == plan
```

- [ ] **步骤 2：运行测试确认失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_analysis_contracts.py -v`

预期：FAIL，`RiskControlPlan` 不存在。

- [ ] **步骤 3：实现契约**

新增 `RiskControlRule`、`RiskControlPlan`，并给 `AnalysisReport` 增加 `risk_controls: RiskControlPlan | None = None`。`to_dict()` 输出 `risk_controls`，`from_dict()` 恢复。

- [ ] **步骤 4：运行测试通过**

同上，预期 PASS。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/domains/analysis/contracts.py services/api/tests/test_analysis_contracts.py
git commit -m "feat: add risk control contracts" -m "Outline:
- Add serializable risk control rule and plan contracts.
- Include optional risk_controls in AnalysisReport payloads.
- Cover risk control round-trip serialization."
```

---

### 任务 2：默认风控策略

**文件：**

- 创建：`services/api/money_api/domains/analysis/risk_policy.py`
- 创建：`services/api/tests/test_risk_policy.py`

- [ ] **步骤 1：编写失败测试**

测试 medium、low、gaps、failed、sell 等场景。

- [ ] **步骤 2：运行测试确认失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_risk_policy.py -v`

预期：FAIL，模块不存在。

- [ ] **步骤 3：实现 DefaultRiskPolicy**

实现 `evaluate(report) -> RiskControlPlan` 和 `apply(report) -> AnalysisReport`。

- [ ] **步骤 4：运行测试通过**

同上，预期 PASS。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/domains/analysis/risk_policy.py services/api/tests/test_risk_policy.py
git commit -m "feat: add default risk policy" -m "Outline:
- Add deterministic risk controls for confidence, status, action, and data gaps.
- Provide report application helper for AnalysisService.
- Cover policy behavior for common risk scenarios."
```

---

### 任务 3：Service/API 集成

**文件：**

- 修改：`services/api/money_api/domains/analysis/service.py`
- 修改：`services/api/tests/test_analysis_service.py`
- 修改：`services/api/tests/test_analysis_api.py`

- [ ] **步骤 1：编写失败测试**

断言 service 和 API 返回 payload 包含 `risk_controls`。

- [ ] **步骤 2：运行测试确认失败**

运行相关测试，预期 FAIL。

- [ ] **步骤 3：集成 DefaultRiskPolicy**

`AnalysisService` 构造函数接受可选 risk policy，默认使用 `DefaultRiskPolicy`。创建报告后、保存前应用。

- [ ] **步骤 4：运行测试通过**

运行 service/api/risk policy 测试。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/domains/analysis/service.py services/api/tests/test_analysis_service.py services/api/tests/test_analysis_api.py
git commit -m "feat: apply risk controls to reports" -m "Outline:
- Apply default risk policy to all reports before persistence.
- Expose risk_controls through service and API payloads.
- Cover service and API risk control behavior."
```

---

### 任务 4：Web mock 契约与文档

**文件：**

- 修改：`apps/web/src/mockData.js`
- 修改：`services/api/tests/test_web_workbench.py`
- 修改：文档文件

- [ ] **步骤 1：补 Web 测试**

检查 mock data 包含 `risk_controls`。

- [ ] **步骤 2：更新 mockData**

为 mock reports 增加 `risk_controls` 字段。

- [ ] **步骤 3：更新 README/stages/backlog/handoff/information-map**

记录阶段 7 第一版完成与回测/组合暂缓。

- [ ] **步骤 4：最终验证**

运行：

```bash
PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -v
node --check apps/web/src/app.js && node --check apps/web/src/mockData.js
```

- [ ] **步骤 5：Commit**

```bash
git add apps/web/src/mockData.js services/api/tests/test_web_workbench.py README.md docs/stages.md docs/improvement-backlog.md docs/agent-handoff.md docs/information-map.md
git commit -m "docs: document risk discipline layer" -m "Outline:
- Add risk_controls to Web mock report payloads.
- Mark stage 7 risk discipline slice complete.
- Record deferred backtesting and portfolio work."
```

---

## 自检结果

- 第一版覆盖风控纪律，不覆盖完整回测/组合。
- 默认策略确定性、离线可测。
- 报告继续保持可序列化和可恢复。
- 投资免责声明作为契约字段输出。
