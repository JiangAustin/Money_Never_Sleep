const reports = Array.isArray(window.MNS_MOCK_REPORTS) ? [...window.MNS_MOCK_REPORTS] : [];
const state = {
  reports,
  selectedTaskId: reports[0]?.task_id || null,
};

const elements = {
  form: document.getElementById("analysis-form"),
  symbol: document.getElementById("symbol-input"),
  message: document.getElementById("message-input"),
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

  elements.detail.append(header, badges, reasons, agents, risks);
}

function renderDiagnostics() {
  elements.diagnostics.replaceChildren();
  const report = getSelectedReport();
  if (!report) {
    elements.diagnostics.append(createElement("p", "empty-state", "暂无诊断信息"));
    return;
  }

  elements.diagnostics.append(createElement("h2", "", "数据诊断"));

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
  renderReportList();
  renderReportDetail();
  renderDiagnostics();
}

function handleSubmit(event) {
  event.preventDefault();
  const report = createLocalAnalysis(elements.symbol.value, elements.message.value);
  state.reports.unshift(report);
  state.selectedTaskId = report.task_id;
  render();
}

elements.form.addEventListener("submit", handleSubmit);
render();
