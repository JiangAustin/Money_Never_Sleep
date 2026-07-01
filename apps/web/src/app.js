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
};

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
    data_gaps: [],
    data_diagnostics: [
      { kind: "web_workbench", source: "local-mock", ok: true, error_type: null, error_message: null, fetched_at: createdAt, is_stale: false },
    ],
    risk_controls: {
      max_position_pct: 0.1,
      stop_loss_pct: 0.08,
      take_profit_pct: 0.15,
      time_horizon: "5-20 个交易日",
      rules: [{ name: "confidence", level: "medium", message: "Web 本地报告默认使用中等置信度风控纪律" }],
      disclaimer: "本报告仅用于研究和复盘，不构成投资建议；任何交易决策需由用户自行承担风险。",
    },
    data_context: {
      stock,
      quote: { price: null, source: "local-mock" },
      technicals: {},
      fundamentals: {},
      news: [],
      gaps: [],
      diagnostics: [],
    },
  };
}

function createFallbackAnalysis(symbol, message, error) {
  const report = createLocalAnalysis(symbol, message);
  report.summary = `${report.summary} HTTP API 暂不可用，已回退到离线 mock。`;
  report.confidence = "low";
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

  const reasons = createElement("section", "detail-section");
  reasons.append(createElement("h3", "", "分析理由"));
  appendList(reasons, report.reasons, "暂无理由");

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

  elements.detail.append(header, badges, reasons, agents, risks, controls);
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

  const context = createElement("section", "diagnostic-section");
  context.append(createElement("h3", "", "Context"));
  const pre = createElement("pre", "context-json");
  pre.textContent = JSON.stringify(report.data_context, null, 2);
  context.append(pre);

  elements.diagnostics.append(gaps, diagnostics, context);
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
