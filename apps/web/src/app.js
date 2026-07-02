const reports = Array.isArray(window.MNS_MOCK_REPORTS) ? [...window.MNS_MOCK_REPORTS] : [];
const state = {
  reports,
  selectedTaskId: reports[0]?.task_id || null,
  apiBaseUrl: getApiBaseUrl(),
  startup: getStartupContext(),
  taskStatus: "当前未提交任务",
  currentTaskId: null,
  currentTaskState: null,
  latestFailedTaskId: null,
  tasks: [],
  researchDebug: {
    reportId: null,
    loading: false,
    error: "",
    tools: [],
  },
  researchDebugRequestId: 0,
};

const researchToolSpecs = [
  { key: "context", label: "Context", endpoint: "/research/context" },
  { key: "quote", label: "Quote", endpoint: "/research/quote" },
  { key: "technicals", label: "Technicals", endpoint: "/research/technicals" },
  { key: "fundamentals", label: "Fundamentals", endpoint: "/research/fundamentals" },
  { key: "news", label: "News", endpoint: "/research/news" },
  { key: "capital_flow", label: "Capital Flow", endpoint: "/research/capital-flow" },
  { key: "longhubang", label: "Longhubang", endpoint: "/research/longhubang" },
  { key: "unlocks", label: "Unlocks", endpoint: "/research/unlocks" },
];

const elements = {
  form: document.getElementById("analysis-form"),
  modePill: document.getElementById("mode-pill"),
  symbol: document.getElementById("symbol-input"),
  message: document.getElementById("message-input"),
  taskStatus: document.getElementById("task-status"),
  taskCancelButton: document.getElementById("task-cancel-button"),
  taskRetryButton: document.getElementById("task-retry-button"),
  taskHistoryList: document.getElementById("task-history-list"),
  reportList: document.getElementById("report-list"),
  reportCount: document.getElementById("report-count"),
  detail: document.getElementById("report-detail"),
  diagnostics: document.getElementById("diagnostics-panel"),
};

function createElement(tagName, className, text) {
  const element = document.createElement(tagName);
  if (className) {
    element.className = className;
  }
  if (text !== undefined) {
    element.textContent = text;
  }
  return element;
}

function normalizeSymbol(symbol) {
  const value = symbol.trim();
  if (!value) {
    return { code: "600519", name: "贵州茅台", market: "cn" };
  }
  if (/^\d{6}$/.test(value)) {
    return { code: value, name: value, market: "cn" };
  }
  const known = {
    贵州茅台: "600519",
    平安银行: "000001",
  };
  return { code: known[value] || value, name: value, market: "cn" };
}

function getApiBaseUrl() {
  const params = new URLSearchParams(window.location.search);
  const api = params.get("api");
  return api ? api.replace(/\/$/, "") : "";
}

function getStartupContext() {
  const startup = window.moneyNeverSleep?.startup;
  if (startup) {
    return startup;
  }
  return {
    mode: "browser-offline",
    apiUrl: "",
    managed: false,
    diagnostics: ["当前在浏览器中直接打开工作台，未附带桌面启动上下文。"],
    lastError: "",
  };
}

function getModeLabel() {
  const mode = state.startup.mode;
  if (mode === "desktop-managed-api") {
    return `桌面托管 API / ${state.startup.apiUrl || state.apiBaseUrl}`;
  }
  if (mode === "desktop-external-api") {
    return `桌面外部 API / ${state.startup.apiUrl || state.apiBaseUrl}`;
  }
  if (mode === "desktop-offline") {
    return "桌面离线模式 / 本地 API 未启动";
  }
  if (state.apiBaseUrl) {
    return `浏览器 API 模式 / ${state.apiBaseUrl}`;
  }
  return "浏览器离线模式 / Mock 预览";
}

function renderModePill() {
  elements.modePill.textContent = getModeLabel();
}

function renderTaskStatus() {
  elements.taskStatus.textContent = state.taskStatus;
  elements.taskCancelButton.disabled = !state.apiBaseUrl || !state.currentTaskId || ["report_ready", "failed", "cancelled"].includes(state.currentTaskState || "");
  elements.taskRetryButton.disabled = !state.apiBaseUrl || !state.latestFailedTaskId;
}

function createLocalAnalysis(symbol, message) {
  const stock = normalizeSymbol(symbol);
  const createdAt = new Date().toISOString();
  const summary = `${stock.name} 的离线分析已生成。当前问题：${message.trim() || "请全面分析并给出投资建议"}`;
  return {
    task_id: `web-${Date.now()}`,
    stock,
    status: "report_ready",
    action: "watch",
    confidence: "medium",
    summary,
    reasons: ["已按 Web 工作台本地 service 生成报告", "字段结构与后端 AnalysisReport 契约保持一致"],
    risks: [{ level: "low", message: "当前为离线 mock 结果，接入 HTTP API 后需重新验证" }],
    agent_views: [
      { agent: "Web Workbench", conclusion: "已创建本地报告并写入最近报告列表" },
      { agent: "Data Contract", conclusion: "报告保留 data_context、gaps 与 diagnostics 字段" },
    ],
    data_sources: ["local-mock"],
    engine_source: "mock",
    engine_mode: "mock",
    fallback_reason: null,
    data_gaps: [],
    data_diagnostics: [
      { kind: "web_workbench", source: "local-mock", ok: true, error_type: null, error_message: null, fetched_at: createdAt, is_stale: false },
    ],
    data_trust: {
      score: 88,
      level: "high",
      summary: "数据可信度高，当前为离线演示结果。",
      signals: ["报告由本地 mock 生成", "字段结构与后端 AnalysisReport 契约保持一致"],
      penalties: ["当前为离线 mock 结果"],
      data_sources: ["local-mock"],
      data_gaps: [],
      diagnostics_ok: 1,
      diagnostics_failed: 0,
      engine_source: "mock",
      engine_mode: "mock",
      fallback_reason: null,
    },
    engine_telemetry: {
      runtime_ms: 18,
      execution_path: "quick",
      cost_tier: "low",
      estimated_request_count: 1,
      engine_source: "mock",
      engine_mode: "mock",
      failure_type: null,
      failure_reason: null,
      notes: ["本地 mock 结果，无真实引擎调用"],
    },
    engine_cost_guardrail: {
      status: "ok",
      summary: "引擎成本处于预算内。",
      alerts: [],
      max_runtime_ms: 5000,
      max_request_count: 1,
      max_cost_tier: "medium",
      runtime_ms: 18,
      estimated_request_count: 1,
      cost_tier: "low",
      engine_source: "mock",
      engine_mode: "mock",
    },
    risk_controls: {
      max_position_pct: 0.1,
      stop_loss_pct: 0.08,
      take_profit_pct: 0.15,
      time_horizon: "5-20 个交易日",
      rules: [{ name: "confidence", level: "medium", message: "Web 本地报告默认使用中等置信度风控纪律" }],
      disclaimer: "本报告仅用于研究和复盘，不构成投资建议；任何交易决策需由用户自行承担风险。",
    },
    investment_plan: {
      direction: "watch",
      target_position_pct: 0.1,
      entry_conditions: ["价格确认站稳后再分批介入"],
      exit_conditions: ["跌破止损线", "核心事件逻辑失效", "目标收益达到"],
      stop_loss_pct: 0.08,
      take_profit_pct: 0.15,
      observation_window: "5-20 个交易日",
      review_conditions: ["每个交易日收盘后复核", "新增结构化事件后立即复核"],
      rationale: ["价格结构保持韧性，但量能确认不足", "存在资金流数据缺口，需要继续观察"],
      positive_evidence_summary: "正向证据主要来自标题与正文同时命中的事件。",
      negative_evidence_summary: "风险证据主要来自正文命中的风险事件。",
      risk_notes: ["短期波动可能放大，需结合真实数据复核"],
    },
    data_context: {
      stock,
      quote: { price: null, source: "local-mock" },
      technicals: {},
      fundamentals: {},
      news: [],
      events: [
        {
          event_type: "earnings_forecast",
          title: "离线演示：示例公司发布业绩预告",
          source: "local-mock",
          summary: "识别为业绩预告类事件，属于高优先级基本面信号。",
          confidence: "medium",
          priority: "high",
          evidence_scope: "title+content",
          evidence_excerpt: "预计同比增长，公告口径保持稳健。",
          time: createdAt.slice(0, 10),
          content: "",
          url: "",
          matched_keywords: ["业绩预告"],
        },
        {
          event_type: "share_repurchase",
          title: "离线演示：示例公司发布股份回购方案",
          source: "local-mock",
          summary: "识别为回购类事件，属于高优先级股东回报信号。",
          confidence: "medium",
          priority: "high",
          evidence_scope: "title",
          evidence_excerpt: "离线演示：示例公司发布股份回购方案",
          time: createdAt.slice(0, 10),
          content: "",
          url: "",
          matched_keywords: ["股份回购"],
        },
        {
          event_type: "share_pledge",
          title: "离线演示：控股股东股权质押进展",
          source: "local-mock",
          summary: "识别为股权质押类事件，属于高优先级风险事件。",
          confidence: "medium",
          priority: "high",
          evidence_scope: "content",
          evidence_excerpt: "控股股东股权质押进展，质押比例出现上升。",
          time: createdAt.slice(0, 10),
          content: "",
          url: "",
          matched_keywords: ["股权质押"],
        },
        {
          event_type: "share_increase",
          title: "离线演示：控股股东拟增持公司股份",
          source: "local-mock",
          summary: "识别为增持类事件，属于高优先级股东增持信号。",
          confidence: "medium",
          priority: "high",
          evidence_scope: "title+content",
          evidence_excerpt: "计划在未来 6 个月内增持不超过 2% 股份。",
          time: createdAt.slice(0, 10),
          content: "",
          url: "",
          matched_keywords: ["增持"],
        },
      ],
      gaps: [],
      diagnostics: [],
    },
  };
}

function createFallbackAnalysis(symbol, message, error) {
  const report = createLocalAnalysis(symbol, message);
  report.summary = `${report.summary} HTTP API 暂不可用，已回退到离线 mock。`;
  report.confidence = "low";
  report.engine_source = "mock";
  report.engine_mode = "auto";
  report.fallback_reason = error.message || "HTTP API request failed";
  report.data_diagnostics.push({
    kind: "http_api",
    source: "web",
    ok: false,
    error_type: error.name || "Error",
    error_message: error.message || "HTTP API request failed",
    fetched_at: new Date().toISOString(),
    is_stale: false,
  });
  return report;
}

async function createHttpAnalysis(apiBaseUrl, symbol, message) {
  const response = await fetch(`${apiBaseUrl}/analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol, message }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

async function createHttpAnalysisTask(apiBaseUrl, symbol, message) {
  const response = await fetch(`${apiBaseUrl}/tasks/analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol, message }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

async function fetchTask(apiBaseUrl, taskId) {
  const response = await fetch(`${apiBaseUrl}/tasks/${taskId}`);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

async function fetchTaskHistory(apiBaseUrl, limit = 10) {
  const response = await fetch(`${apiBaseUrl}/tasks?limit=${limit}`);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

async function cancelHttpAnalysisTask(apiBaseUrl, taskId) {
  const response = await fetch(`${apiBaseUrl}/tasks/${taskId}/cancel`, { method: "POST" });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

async function retryHttpAnalysisTask(apiBaseUrl, taskId) {
  const response = await fetch(`${apiBaseUrl}/tasks/${taskId}/retry`, { method: "POST" });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

async function fetchReport(apiBaseUrl, reportId) {
  const response = await fetch(`${apiBaseUrl}/reports/${reportId}`);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

async function fetchResearchTool(apiBaseUrl, endpoint, symbol) {
  const response = await fetch(`${apiBaseUrl}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

function delay(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function pollAnalysisTask(apiBaseUrl, taskId) {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    const task = await fetchTask(apiBaseUrl, taskId);
    state.currentTaskId = task.task_id;
    state.currentTaskState = task.status;
    state.taskStatus = `任务状态：${task.status}`;
    renderTaskStatus();
    if (task.status === "report_ready" && task.report_id) {
      state.currentTaskId = null;
      state.currentTaskState = task.status;
      state.taskStatus = "任务已完成";
      renderTaskStatus();
      return fetchReport(apiBaseUrl, task.report_id);
    }
    if (task.status === "failed") {
      state.currentTaskId = null;
      state.currentTaskState = task.status;
      state.latestFailedTaskId = task.task_id;
      throw new Error(task.error || "analysis task failed");
    }
    if (task.status === "cancelled") {
      state.currentTaskId = null;
      state.currentTaskState = task.status;
      state.latestFailedTaskId = task.task_id;
      throw new Error(task.error || "analysis task cancelled");
    }
    await delay(250);
  }
  throw new Error("analysis task timeout");
}

function getSelectedReport() {
  return state.reports.find((report) => report.task_id === state.selectedTaskId) || state.reports[0] || null;
}

function renderReportList() {
  elements.reportList.replaceChildren();
  elements.reportCount.textContent = String(state.reports.length);

  if (state.reports.length === 0) {
    elements.reportList.append(createElement("p", "empty-state", "暂无报告"));
    return;
  }

  state.reports.forEach((report) => {
    const button = createElement("button", "report-item");
    button.type = "button";
    button.dataset.taskId = report.task_id;
    button.classList.toggle("is-active", report.task_id === state.selectedTaskId);

    const title = createElement("span", "report-title", `${report.stock.name} ${report.action.toUpperCase()}`);
    const meta = createElement("span", "report-meta", `${report.confidence} / ${report.status}`);
    const summary = createElement("span", "report-summary", report.summary);
    button.append(title, meta, summary);
    button.addEventListener("click", () => {
      state.selectedTaskId = report.task_id;
      render();
    });
    elements.reportList.append(button);
  });
}

function renderTaskHistory() {
  elements.taskHistoryList.replaceChildren();
  if (!state.apiBaseUrl) {
    elements.taskHistoryList.append(createElement("p", "empty-state", "离线模式下不显示真实任务历史"));
    return;
  }
  if (!state.tasks.length) {
    elements.taskHistoryList.append(createElement("p", "empty-state", "暂无任务历史"));
    return;
  }

  state.tasks.forEach((task) => {
    const item = createElement("article", "report-item");
    const retryMeta = task.next_retry_at
      ? `下次重试 ${task.next_retry_at}${task.next_retry_policy ? ` / 策略 ${task.next_retry_policy}` : ""}${Number.isInteger(task.next_retry_delay_s) ? ` / 延迟 ${task.next_retry_delay_s}s` : ""}`
      : task.error || task.message || "任务已创建";
    item.append(
      createElement("span", "report-title", `${task.symbol} / ${task.status}`),
      createElement("span", "report-meta", task.task_id),
      createElement("span", "report-summary", retryMeta)
    );
    elements.taskHistoryList.append(item);
  });
}

function appendList(parent, items, emptyText, itemClassName) {
  if (!items || items.length === 0) {
    parent.append(createElement("p", "empty-state", emptyText));
    return;
  }
  const list = createElement("ul", itemClassName || "detail-list");
  items.forEach((item) => {
    const li = createElement("li", "");
    if (typeof item === "string") {
      li.textContent = item;
    } else {
      li.textContent = item.message || item.conclusion || item.title || JSON.stringify(item);
    }
    list.append(li);
  });
  parent.append(list);
}

function renderStructuredEvents(parent, events) {
  if (!events || events.length === 0) {
    parent.append(createElement("p", "empty-state", "暂无结构化事件"));
    return;
  }

  events.forEach((event) => {
    const card = createElement("article", "event-card");
    card.append(
      createElement("strong", "", `${event.event_type} / ${event.priority || "medium"} / ${event.source}`),
      createElement("p", "", event.title),
      createElement("p", "empty-state", event.summary || ""),
      createElement("small", "", `证据范围：${event.evidence_scope || "title"}`),
      createElement("small", "", event.evidence_excerpt ? `证据片段：${event.evidence_excerpt}` : "无证据片段"),
      createElement(
        "small",
        "",
        event.matched_keywords && event.matched_keywords.length ? `关键词：${event.matched_keywords.join("、")}` : "未匹配关键词"
      )
    );
    parent.append(card);
  });
}

function renderInvestmentPlan(parent, plan) {
  parent.append(createElement("h3", "", "投资计划"));
  if (!plan) {
    parent.append(createElement("p", "empty-state", "暂无投资计划"));
    return;
  }

  parent.append(
    createElement(
      "p",
      "summary",
      `方向 ${plan.direction || "unknown"} / 仓位 ${(Number(plan.target_position_pct || 0) * 100).toFixed(1)}% / 止损 ${(Number(plan.stop_loss_pct || 0) * 100).toFixed(1)}% / 止盈 ${(Number(plan.take_profit_pct || 0) * 100).toFixed(1)}%`
    ),
    createElement("p", "empty-state", `观察窗口：${plan.observation_window || "暂无"}`)
  );

  const entry = createElement("section", "plan-subsection");
  entry.append(createElement("h4", "", "入场条件"));
  appendList(entry, plan.entry_conditions, "暂无入场条件");

  const exit = createElement("section", "plan-subsection");
  exit.append(createElement("h4", "", "退出条件"));
  appendList(exit, plan.exit_conditions, "暂无退出条件");

  const review = createElement("section", "plan-subsection");
  review.append(createElement("h4", "", "复核条件"));
  appendList(review, plan.review_conditions, "暂无复核条件");

  const rationale = createElement("section", "plan-subsection");
  rationale.append(createElement("h4", "", "计划依据"));
  appendList(rationale, plan.rationale, "暂无计划依据");

  const evidence = createElement("section", "plan-subsection");
  evidence.append(createElement("h4", "", "证据来源"));
  appendList(
    evidence,
    [plan.positive_evidence_summary, plan.negative_evidence_summary].filter(Boolean),
    "暂无证据来源说明"
  );

  const notes = createElement("section", "plan-subsection");
  notes.append(createElement("h4", "", "风险备注"));
  appendList(notes, plan.risk_notes, "暂无风险备注");

  parent.append(entry, exit, review, rationale, evidence, notes);
}

function renderDataTrust(parent, trust) {
  parent.append(createElement("h3", "", "数据可信度"));
  if (!trust) {
    parent.append(createElement("p", "empty-state", "暂无数据可信度评分"));
    return;
  }

  parent.append(
    createElement("p", "summary", `${trust.level || "unknown"} / ${trust.score ?? "?"} 分`),
    createElement("p", "empty-state", trust.summary || "暂无可信度说明")
  );

  const signals = createElement("section", "plan-subsection");
  signals.append(createElement("h4", "", "正向信号"));
  appendList(signals, trust.signals, "暂无正向信号");

  const penalties = createElement("section", "plan-subsection");
  penalties.append(createElement("h4", "", "扣分项"));
  appendList(penalties, trust.penalties, "暂无扣分项");

  const meta = createElement("section", "plan-subsection");
  meta.append(createElement("h4", "", "可信度元数据"));
  appendList(
    meta,
    [
      `数据来源：${Array.isArray(trust.data_sources) && trust.data_sources.length ? trust.data_sources.join("、") : "暂无"}`,
      `数据缺口：${Array.isArray(trust.data_gaps) && trust.data_gaps.length ? trust.data_gaps.join("、") : "无"}`,
      `诊断成功：${Number(trust.diagnostics_ok || 0)}`,
      `诊断失败：${Number(trust.diagnostics_failed || 0)}`,
      `引擎：${trust.engine_mode || "unknown"} / ${trust.engine_source || "unknown"}`,
    ],
    "暂无可信度元数据"
  );

  parent.append(signals, penalties, meta);
}

function renderEngineTelemetry(parent, telemetry) {
  parent.append(createElement("h3", "", "引擎治理"));
  if (!telemetry) {
    parent.append(createElement("p", "empty-state", "暂无引擎运行画像"));
    return;
  }

  parent.append(
    createElement(
      "p",
      "summary",
      `路径 ${telemetry.execution_path || "unknown"} / 成本 ${telemetry.cost_tier || "low"} / 耗时 ${Number(telemetry.runtime_ms || 0)}ms / 请求 ${Number(telemetry.estimated_request_count || 0)}`
    ),
    createElement("p", "empty-state", `引擎 ${telemetry.engine_mode || "unknown"} / ${telemetry.engine_source || "unknown"}`)
  );

  const failures = createElement("section", "plan-subsection");
  failures.append(createElement("h4", "", "失败信息"));
  appendList(
    failures,
    [
      telemetry.failure_type ? `失败类型：${telemetry.failure_type}` : "无失败类型",
      telemetry.failure_reason ? `失败原因：${telemetry.failure_reason}` : "无失败原因",
    ],
    "暂无失败信息"
  );

  const notes = createElement("section", "plan-subsection");
  notes.append(createElement("h4", "", "治理备注"));
  appendList(notes, telemetry.notes, "暂无治理备注");

  parent.append(failures, notes);
}

function renderEngineCostGuardrail(parent, guardrail) {
  parent.append(createElement("h3", "", "成本阈值"));
  if (!guardrail) {
    parent.append(createElement("p", "empty-state", "暂无成本阈值信息"));
    return;
  }

  parent.append(
    createElement(
      "p",
      "summary",
      `状态 ${guardrail.status || "unknown"} / 预算 ${guardrail.max_cost_tier || "medium"} / 阈值 ${Number(guardrail.max_runtime_ms || 0)}ms`
    ),
    createElement("p", "empty-state", guardrail.summary || "暂无成本阈值说明")
  );

  const alerts = createElement("section", "plan-subsection");
  alerts.append(createElement("h4", "", "告警"));
  appendList(alerts, guardrail.alerts, "暂无告警");

  const meta = createElement("section", "plan-subsection");
  meta.append(createElement("h4", "", "阈值元数据"));
  appendList(
    meta,
    [
      `runtime_ms：${Number(guardrail.runtime_ms || 0)}`,
      `estimated_request_count：${Number(guardrail.estimated_request_count || 0)}`,
      `cost_tier：${guardrail.cost_tier || "low"}`,
      `引擎：${guardrail.engine_mode || "unknown"} / ${guardrail.engine_source || "unknown"}`,
    ],
    "暂无阈值元数据"
  );

  parent.append(alerts, meta);
}

function formatDisplayValue(value, digits = 2) {
  if (value === null || value === undefined || value === "") {
    return "暂无";
  }
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return String(value);
  }
  return Number.isInteger(numeric) ? String(numeric) : numeric.toFixed(digits);
}

function getResearchSignalSummary(report) {
  if (!state.apiBaseUrl || state.researchDebug.reportId !== report.task_id || state.researchDebug.loading) {
    return {
      heading: "研究信号",
      summary: "研究工具数据尚未就绪，暂时无法生成与计划对齐的联动摘要。",
      items: [],
    };
  }

  const toolMap = new Map(state.researchDebug.tools.map((entry) => [entry.spec.key, entry]));
  const items = [];
  let positive = 0;
  let negative = 0;

  const capitalFlowEntry = toolMap.get("capital_flow");
  if (capitalFlowEntry?.ok) {
    const rows = capitalFlowEntry.payload?.result?.data?.rows || [];
    const firstRow = rows[0] || {};
    const inflow = Number(firstRow.MAIN_NET_INFLOW);
    if (Number.isFinite(inflow)) {
      if (inflow > 0) positive += 1;
      if (inflow < 0) negative += 1;
      items.push(`资金流：主力净流入 ${formatDisplayValue(firstRow.MAIN_NET_INFLOW)}，${inflow > 0 ? "偏强" : inflow < 0 ? "偏弱" : "中性"}。`);
    }
  }

  const longhubangEntry = toolMap.get("longhubang");
  if (longhubangEntry?.ok) {
    const rows = longhubangEntry.payload?.result?.data?.rows || [];
    const firstRow = rows[0] || {};
    const netAmt = Number(firstRow.NET_AMT);
    if (Number.isFinite(netAmt)) {
      if (netAmt > 0) positive += 1;
      if (netAmt < 0) negative += 1;
      items.push(`龙虎榜：净额 ${formatDisplayValue(firstRow.NET_AMT)}，${netAmt > 0 ? "净流入" : netAmt < 0 ? "净流出" : "持平"}。`);
    }
  }

  const unlocksEntry = toolMap.get("unlocks");
  if (unlocksEntry?.ok) {
    const rows = unlocksEntry.payload?.result?.data?.rows || [];
    const firstRow = rows[0] || {};
    const unlockRatio = Number(firstRow.UNLOCK_RATIO);
    if (Number.isFinite(unlockRatio)) {
      if (unlockRatio >= 3) negative += 1;
      items.push(`解禁：${firstRow.UNLOCK_DATE || "暂无日期"}，比例 ${formatDisplayValue(firstRow.UNLOCK_RATIO)}%，${unlockRatio >= 3 ? "需要关注供给压力" : "压力可控"}。`);
    }
  }

  const newsEntry = toolMap.get("news");
  if (newsEntry?.ok) {
    const rows = Array.isArray(newsEntry.payload?.result?.data) ? newsEntry.payload.result.data : [];
    const bulletinHit = rows.find((item) => String(item.source || "").includes("公告"));
    if (bulletinHit?.title) {
      items.push(`公告：最新公告线索为「${bulletinHit.title}」。`);
    }
  }

  const contextEntry = toolMap.get("context");
  if (contextEntry?.ok) {
    const eventCount = Array.isArray(contextEntry.payload?.data_context?.events) ? contextEntry.payload.data_context.events.length : 0;
    items.push(`结构化事件：当前上下文已抽取 ${eventCount} 条事件。`);
  }

  const plan = report.investment_plan || {};
  const planDirection = String(plan.direction || "unknown");
  const targetPosition = formatDisplayValue(plan.target_position_pct * 100, 1);
  const stopLoss = formatDisplayValue(plan.stop_loss_pct * 100, 1);
  const takeProfit = formatDisplayValue(plan.take_profit_pct * 100, 1);

  let summary = `当前计划方向 ${planDirection}，目标仓位 ${targetPosition}%，止损 ${stopLoss}% / 止盈 ${takeProfit}%。暂无可用研究信号。`;
  if (positive > negative && positive > 0) {
    summary = `当前计划方向 ${planDirection}，目标仓位 ${targetPosition}%，止损 ${stopLoss}% / 止盈 ${takeProfit}%。资金流与榜单信号偏正向（正向 ${positive}，负向 ${negative}），可支撑更主动的观察。`;
  } else if (negative > positive && negative > 0) {
    summary = `当前计划方向 ${planDirection}，目标仓位 ${targetPosition}%，止损 ${stopLoss}% / 止盈 ${takeProfit}%。资金流与榜单信号偏谨慎（正向 ${positive}，负向 ${negative}），计划应保持收缩。`;
  } else if (positive > 0 || negative > 0) {
    summary = `当前计划方向 ${planDirection}，目标仓位 ${targetPosition}%，止损 ${stopLoss}% / 止盈 ${takeProfit}%。资金流与榜单信号中性偏混合（正向 ${positive}，负向 ${negative}）。`;
  }

  const planAlignment = (() => {
    const bullishPlan = planDirection === "buy" || planDirection === "watch";
    const bearishPlan = planDirection === "wait" || planDirection === "sell";
    if (positive > negative && bullishPlan) {
      return "计划与研究信号一致：偏正向信号支持当前计划。";
    }
    if (negative > positive && bearishPlan) {
      return "计划与研究信号一致：风险信号支持当前收缩/观望。";
    }
    if (positive > 0 || negative > 0) {
      return "计划与研究信号存在轻微分歧，需要保持复核。";
    }
    return "研究信号不足，当前计划主要依赖既有风险纪律。";
  })();

  items.unshift(`计划对齐：${planAlignment}`);

  return {
    heading: "研究信号",
    summary,
    items,
  };
}

function getResearchToolSummaryLines(spec, result) {
  if (spec.key === "context") {
    return [
      `数据来源：${Array.isArray(result.data_sources) && result.data_sources.length ? result.data_sources.join("、") : "暂无"}`,
      `来源链：${Array.isArray(result.source_summary) && result.source_summary.length ? result.source_summary.map((item) => `${item.kind || "?"}:${item.source || "?"}`).join("、") : "暂无"}`,
      `事件数：${Array.isArray(result.data_context?.events) ? result.data_context.events.length : 0}`,
    ];
  }

  const payload = result.result || {};
  const data = payload.data || {};
  const rows = Array.isArray(data.rows) ? data.rows : [];
  const firstRow = rows[0] || {};

  if (spec.key === "quote") {
    return [
      `来源：${payload.source || "unknown"} / 状态：${payload.ok ? "ok" : "failed"}`,
      `最新价：${formatDisplayValue(data.price ?? data.latest_close)}`,
      `涨跌幅：${formatDisplayValue(data.change_pct ?? data.change_5d_pct)}%`,
    ];
  }

  if (spec.key === "technicals") {
    return [
      `来源：${payload.source || "unknown"} / 状态：${payload.ok ? "ok" : "failed"}`,
      `MA5：${formatDisplayValue(data.ma5)} / MA10：${formatDisplayValue(data.ma10)} / MA20：${formatDisplayValue(data.ma20)}`,
      `样本数：${formatDisplayValue(data.sample_size, 0)}`,
    ];
  }

  if (spec.key === "fundamentals") {
    const latest = data.latest_finance || {};
    return [
      `来源：${payload.source || "unknown"} / 状态：${payload.ok ? "ok" : "failed"}`,
      `最新报告：${latest.report_date || "暂无"} / EPS：${formatDisplayValue(latest.eps)} / PE：${formatDisplayValue(data.latest_valuation?.pe)}`,
      `收入同比：${formatDisplayValue(latest.revenue_yoy)}% / 净利同比：${formatDisplayValue(latest.net_profit_yoy)}%`,
    ];
  }

  if (spec.key === "news") {
    return [
      `来源：${payload.source || "unknown"} / 状态：${payload.ok ? "ok" : "failed"}`,
      `资讯条数：${Array.isArray(data) ? data.length : 0}`,
      `首条：${Array.isArray(data) && data.length ? data[0].title || "暂无标题" : "暂无"}`,
    ];
  }

  if (spec.key === "capital_flow") {
    return [
      `来源：${payload.source || "unknown"} / 状态：${payload.ok ? "ok" : "failed"}`,
      `主力净流入：${formatDisplayValue(firstRow.MAIN_NET_INFLOW)} / 净流入率：${formatDisplayValue(firstRow.MAIN_NET_INFLOW_RATE)}%`,
      `主买：${formatDisplayValue(firstRow.MAIN_BUY)} / 主卖：${formatDisplayValue(firstRow.MAIN_SELL)} / 行数：${rows.length}`,
    ];
  }

  if (spec.key === "longhubang") {
    const netAmt = Number(firstRow.NET_AMT);
    const netDirection = Number.isFinite(netAmt) ? (netAmt > 0 ? "净流入" : netAmt < 0 ? "净流出" : "持平") : "暂无方向";
    return [
      `来源：${payload.source || "unknown"} / 状态：${payload.ok ? "ok" : "failed"}`,
      `龙虎榜净额：${formatDisplayValue(firstRow.NET_AMT)}（${netDirection}）`,
      `买额：${formatDisplayValue(firstRow.BUY_AMT)} / 卖额：${formatDisplayValue(firstRow.SELL_AMT)} / 机构买额：${formatDisplayValue(firstRow.ORGAN_AMT)}`,
      `行数：${rows.length}`,
    ];
  }

  if (spec.key === "unlocks") {
    return [
      `来源：${payload.source || "unknown"} / 状态：${payload.ok ? "ok" : "failed"}`,
      `解禁日期：${firstRow.UNLOCK_DATE || "暂无"} / 解禁数量：${formatDisplayValue(firstRow.UNLOCK_NUM)} / 解禁比例：${formatDisplayValue(firstRow.UNLOCK_RATIO)}%`,
      `解禁市值：${formatDisplayValue(firstRow.UNLOCK_VALUE)} / 行数：${rows.length}`,
    ];
  }

  return [
    `来源：${payload.source || "unknown"} / 状态：${payload.ok ? "ok" : "failed"}`,
    `数据行数：${rows.length}`,
    `摘要：${data.summary ? JSON.stringify(data.summary) : "暂无"}`,
  ];
}

function renderResearchToolResult(parent, spec, result) {
  const card = createElement("details", "research-tool-card");
  const summary = createElement("summary", "", spec.label);
  const meta = createElement("p", "empty-state");
  const summarySection = createElement("section", "plan-subsection");

  if (spec.key === "context") {
    meta.textContent = `数据来源：${Array.isArray(result.data_sources) && result.data_sources.length ? result.data_sources.join("、") : "暂无"} / 路径：${Array.isArray(result.source_summary) && result.source_summary.length ? result.source_summary.map((item) => `${item.kind || "?"}:${item.source || "?"}`).join("、") : "暂无"}`;
  } else {
    const payload = result.result || {};
    meta.textContent = `引擎：${payload.source || "unknown"} / 状态：${payload.ok ? "ok" : "failed"}`;
  }

  summarySection.append(createElement("h4", "", "摘要"));
  appendList(summarySection, getResearchToolSummaryLines(spec, result), "暂无摘要");

  const pre = createElement("pre", "context-json");
  pre.textContent = JSON.stringify(result, null, 2);
  card.append(summary, meta, summarySection, pre);
  parent.append(card);
}

async function loadResearchDebug(report, requestId) {
  const symbol = report.stock?.code || report.stock?.name || "";
  const settled = await Promise.all(
    researchToolSpecs.map(async (spec) => {
      try {
        const payload = await fetchResearchTool(state.apiBaseUrl, spec.endpoint, symbol);
        return { spec, ok: true, payload };
      } catch (error) {
        return { spec, ok: false, error: error.message || "unknown error" };
      }
    })
  );

  if (requestId !== state.researchDebugRequestId || state.selectedTaskId !== report.task_id) {
    return;
  }

  state.researchDebug = {
    reportId: report.task_id,
    loading: false,
    error: "",
    tools: settled,
  };
  render();
}

function renderResearchDebug(parent, report) {
  parent.append(createElement("h3", "", "研究工具调试"));

  if (!state.apiBaseUrl) {
    parent.append(createElement("p", "empty-state", "当前为离线模式，无法调用真实研究工具接口。"));
    return;
  }

  if (state.researchDebug.reportId !== report.task_id) {
    state.researchDebugRequestId += 1;
    state.researchDebug = {
      reportId: report.task_id,
      loading: true,
      error: "",
      tools: [],
    };
    window.setTimeout(() => {
      void loadResearchDebug(report, state.researchDebugRequestId);
    }, 0);
  }

  if (state.researchDebug.loading) {
    parent.append(createElement("p", "empty-state", `正在拉取 ${report.stock.code} 的研究工具返回值...`));
    return;
  }

  if (state.researchDebug.error) {
    parent.append(createElement("p", "empty-state", state.researchDebug.error));
    return;
  }

  if (!state.researchDebug.tools.length) {
    parent.append(createElement("p", "empty-state", "暂无研究工具返回值"));
    return;
  }

  state.researchDebug.tools.forEach((entry) => {
    if (entry.ok) {
      renderResearchToolResult(parent, entry.spec, entry.payload);
    } else {
      const card = createElement("article", "research-tool-card");
      card.append(
        createElement("strong", "", entry.spec.label),
        createElement("p", "empty-state", `调用失败：${entry.error}`)
      );
      parent.append(card);
    }
  });
}

function renderReportDetail() {
  elements.detail.replaceChildren();
  const report = getSelectedReport();
  if (!report) {
    elements.detail.append(createElement("p", "empty-state", "选择或创建一份报告"));
    return;
  }

  const header = createElement("div", "detail-header");
  header.append(
    createElement("p", "eyebrow", report.stock.code),
    createElement("h2", "", report.stock.name),
    createElement("p", "summary", report.summary)
  );

  const badges = createElement("div", "badge-row");
  badges.append(
    createElement("span", "status-badge", `状态 ${report.status}`),
    createElement("span", "status-badge", `动作 ${report.action}`),
    createElement("span", "status-badge", `置信度 ${report.confidence}`)
  );

  const provenance = createElement("section", "detail-section");
  provenance.append(createElement("h3", "", "来源与引擎"));
  provenance.append(
    createElement("p", "summary", `引擎 ${report.engine_mode || "unknown"} / ${report.engine_source || "unknown"}`),
    createElement(
      "p",
      "empty-state",
      `数据来源：${Array.isArray(report.data_sources) && report.data_sources.length > 0 ? report.data_sources.join("、") : "暂无"}`
    )
  );
  if (report.fallback_reason) {
    provenance.append(createElement("p", "empty-state", `回退原因：${report.fallback_reason}`));
  }

  const signalSummary = getResearchSignalSummary(report);
  const signals = createElement("section", "detail-section");
  signals.append(createElement("h3", "", signalSummary.heading));
  signals.append(createElement("p", "summary", signalSummary.summary));
  appendList(signals, signalSummary.items, "暂无研究信号");

  const reasons = createElement("section", "detail-section");
  reasons.append(createElement("h3", "", "分析理由"));
  appendList(reasons, report.reasons, "暂无理由");

  const events = createElement("section", "detail-section");
  events.append(createElement("h3", "", "结构化事件"));
  renderStructuredEvents(events, report.data_context.events || []);

  const investment = createElement("section", "detail-section");
  renderInvestmentPlan(investment, report.investment_plan);

  const trust = createElement("section", "detail-section");
  renderDataTrust(trust, report.data_trust);

  const telemetry = createElement("section", "detail-section");
  renderEngineTelemetry(telemetry, report.engine_telemetry);

  const guardrail = createElement("section", "detail-section");
  renderEngineCostGuardrail(guardrail, report.engine_cost_guardrail);

  const agents = createElement("section", "detail-section");
  agents.append(createElement("h3", "", "Agent 视角"));
  if (report.agent_views.length === 0) {
    agents.append(createElement("p", "empty-state", "暂无 Agent 视角"));
  } else {
    report.agent_views.forEach((view) => {
      const card = createElement("article", "agent-card");
      card.append(createElement("strong", "", view.agent), createElement("p", "", view.conclusion));
      agents.append(card);
    });
  }

  const risks = createElement("section", "detail-section");
  risks.append(createElement("h3", "", "风险提示"));
  appendList(risks, report.risks, "暂无风险提示", "risk-list");

  const controls = createElement("section", "detail-section");
  controls.append(createElement("h3", "", "风控纪律"));
  if (report.risk_controls) {
    const plan = report.risk_controls;
    controls.append(
      createElement("p", "summary", `仓位上限 ${(plan.max_position_pct * 100).toFixed(1)}% / 止损 ${(plan.stop_loss_pct * 100).toFixed(1)}% / 止盈 ${(plan.take_profit_pct * 100).toFixed(1)}%`)
    );
    appendList(controls, plan.rules, "暂无风控规则");
    controls.append(createElement("p", "empty-state", plan.disclaimer));
  } else {
    controls.append(createElement("p", "empty-state", "暂无风控计划"));
  }

  elements.detail.append(header, badges, provenance, signals, reasons, events, investment, trust, telemetry, guardrail, agents, risks, controls);
}

function renderDiagnostics() {
  elements.diagnostics.replaceChildren();
  const report = getSelectedReport();

  elements.diagnostics.append(createElement("h2", "", "数据诊断"));

  const startupSection = createElement("section", "diagnostic-section startup-diagnostics");
  startupSection.append(createElement("h3", "", "启动模式"));
  startupSection.append(createElement("p", "summary", getModeLabel()));
  appendList(startupSection, state.startup.diagnostics || [], "暂无启动诊断");
  if (state.startup.lastError) {
    startupSection.append(createElement("p", "empty-state", `最近错误：${state.startup.lastError}`));
  }
  elements.diagnostics.append(startupSection);

  if (!report) {
    elements.diagnostics.append(createElement("p", "empty-state", "暂无报告级诊断信息"));
    return;
  }

  const gaps = createElement("section", "diagnostic-section");
  gaps.append(createElement("h3", "", "Data gaps"));
  appendList(gaps, report.data_gaps, "无数据缺口");

  const diagnostics = createElement("section", "diagnostic-section");
  diagnostics.append(createElement("h3", "", "Diagnostics"));
  if (report.data_diagnostics.length === 0) {
    diagnostics.append(createElement("p", "empty-state", "暂无诊断记录"));
  } else {
    report.data_diagnostics.forEach((diagnostic) => {
      const row = createElement("div", "diagnostic-row");
      row.append(
        createElement("span", diagnostic.ok ? "dot ok" : "dot warn"),
        createElement("span", "", `${diagnostic.kind} / ${diagnostic.source}`),
        createElement("small", "", diagnostic.ok ? "ok" : diagnostic.error_message || "failed")
      );
      diagnostics.append(row);
    });
  }

  const eventSection = createElement("section", "diagnostic-section");
  eventSection.append(createElement("h3", "", "结构化事件"));
  renderStructuredEvents(eventSection, report.data_context.events || []);

  const context = createElement("section", "diagnostic-section");
  context.append(createElement("h3", "", "Context"));
  const pre = createElement("pre", "context-json");
  pre.textContent = JSON.stringify(report.data_context, null, 2);
  context.append(pre);

  const researchDebug = createElement("section", "diagnostic-section");
  renderResearchDebug(researchDebug, report);

  elements.diagnostics.append(gaps, diagnostics, eventSection, researchDebug, context);
}

function render() {
  renderModePill();
  renderTaskStatus();
  renderReportList();
  renderTaskHistory();
  renderReportDetail();
  renderDiagnostics();
}

async function refreshTaskHistory() {
  if (!state.apiBaseUrl) {
    state.tasks = [];
    renderTaskHistory();
    return;
  }
  try {
    state.tasks = await fetchTaskHistory(state.apiBaseUrl, 10);
  } catch {
    state.tasks = [];
  }
  renderTaskHistory();
}

async function handleSubmit(event) {
  event.preventDefault();
  let report;
  if (state.apiBaseUrl) {
    try {
      const task = await createHttpAnalysisTask(state.apiBaseUrl, elements.symbol.value, elements.message.value);
      state.currentTaskId = task.task_id;
      state.currentTaskState = task.status;
      state.latestFailedTaskId = null;
      state.taskStatus = `任务已创建：${task.task_id}`;
      renderTaskStatus();
      await refreshTaskHistory();
      report = await pollAnalysisTask(state.apiBaseUrl, task.task_id);
    } catch (error) {
      state.taskStatus = `任务失败：${error.message || "unknown error"}`;
      renderTaskStatus();
      report = createFallbackAnalysis(elements.symbol.value, elements.message.value, error);
    }
  } else {
    state.taskStatus = "当前为离线本地模式";
    report = createLocalAnalysis(elements.symbol.value, elements.message.value);
  }
  state.reports.unshift(report);
  state.selectedTaskId = report.task_id;
  render();
}

async function handleCancelTask() {
  if (!state.apiBaseUrl || !state.currentTaskId) {
    return;
  }
  try {
    const task = await cancelHttpAnalysisTask(state.apiBaseUrl, state.currentTaskId);
    state.currentTaskId = null;
    state.currentTaskState = task.status;
    state.latestFailedTaskId = task.task_id;
    state.taskStatus = "任务已取消";
    renderTaskStatus();
    await refreshTaskHistory();
  } catch (error) {
    state.taskStatus = `取消失败：${error.message || "unknown error"}`;
    renderTaskStatus();
  }
}

async function handleRetryTask() {
  if (!state.apiBaseUrl || !state.latestFailedTaskId) {
    return;
  }
  try {
    const task = await retryHttpAnalysisTask(state.apiBaseUrl, state.latestFailedTaskId);
    state.currentTaskId = task.task_id;
    state.currentTaskState = task.status;
    state.latestFailedTaskId = null;
    state.taskStatus = `任务已重试：${task.task_id}`;
    renderTaskStatus();
    await refreshTaskHistory();
    const report = await pollAnalysisTask(state.apiBaseUrl, task.task_id);
    state.reports.unshift(report);
    state.selectedTaskId = report.task_id;
    render();
  } catch (error) {
    state.taskStatus = `重试失败：${error.message || "unknown error"}`;
    renderTaskStatus();
  }
}

elements.form.addEventListener("submit", handleSubmit);
elements.taskCancelButton.addEventListener("click", handleCancelTask);
elements.taskRetryButton.addEventListener("click", handleRetryTask);
render();
refreshTaskHistory();
