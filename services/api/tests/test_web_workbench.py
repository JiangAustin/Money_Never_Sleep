from pathlib import Path


WEB_ROOT = Path("apps/web")


def read_web_file(relative_path: str) -> str:
    return (WEB_ROOT / relative_path).read_text(encoding="utf-8")


def test_web_workbench_entry_references_assets() -> None:
    html = read_web_file("index.html")

    assert '<link rel="stylesheet" href="src/styles.css">' in html
    assert '<script src="src/mockData.js"></script>' in html
    assert '<script src="src/app.js"></script>' in html


def test_web_workbench_has_core_regions() -> None:
    html = read_web_file("index.html")

    assert 'id="analysis-form"' in html
    assert 'id="report-list"' in html
    assert 'id="report-detail"' in html
    assert 'id="diagnostics-panel"' in html
    assert 'id="mode-pill"' in html
    assert 'id="task-status"' in html
    assert 'id="task-cancel-button"' in html
    assert 'id="task-retry-button"' in html
    assert 'id="task-history-search"' in html
    assert 'id="task-history-filters"' in html
    assert 'id="task-history-detail"' in html
    assert 'id="task-history-list"' in html


def test_mock_data_matches_report_contract() -> None:
    mock_data = read_web_file("src/mockData.js")

    for field in (
        "task_id",
        "stock",
        "status",
        "action",
        "confidence",
        "summary",
        "reasons",
        "risks",
        "agent_views",
        "data_gaps",
        "data_diagnostics",
        "data_sources",
        "engine_source",
        "engine_mode",
        "fallback_reason",
        "data_context",
        "evidence_scope",
        "evidence_excerpt",
        "risk_controls",
        "investment_plan",
        "data_trust",
        "engine_telemetry",
        "engine_cost_guardrail",
        "backtest",
        "events",
    ):
        assert field in mock_data

    assert "window.MNS_MOCK_REPORTS" in mock_data


def test_app_js_exposes_service_and_render_boundaries() -> None:
    app_js = read_web_file("src/app.js")

    assert "function createLocalAnalysis" in app_js
    assert "function renderReportList" in app_js
    assert "function renderReportDetail" in app_js
    assert "function renderDiagnostics" in app_js
    assert "function renderResearchDebug" in app_js
    assert "function fetchResearchTool" in app_js
    assert "function getResearchToolSummaryLines" in app_js
    assert "function getStartupContext" in app_js
    assert "function renderModePill" in app_js
    assert "function renderTaskHistoryFilters" in app_js
    assert "function renderTaskHistoryDetail" in app_js
    assert "function getTaskHistoryFilterOptions" in app_js
    assert "function getTaskHistoryDetail" in app_js
    assert "function getPlanEvidenceSummary" in app_js
    assert "function renderTaskHistorySearch" in app_js
    assert "analysis-form" in app_js
    assert "taskHistoryFilter" in app_js
    assert "taskHistorySearch" in app_js
    assert "selectedTaskHistoryId" in app_js
    assert "filterTaskHistory" in app_js
    assert "risk_controls" in app_js
    assert "investment_plan" in app_js
    assert "data_trust" in app_js
    assert "engine_telemetry" in app_js
    assert "engine_cost_guardrail" in app_js
    assert "evidence_scope" in app_js
    assert "evidence_excerpt" in app_js
    assert "engine_source" in app_js
    assert "data_sources" in app_js
    assert "renderStructuredEvents" in app_js
    assert "/research/context" in app_js
    assert "/research/quote" in app_js
    assert "/research/technicals" in app_js
    assert "/research/fundamentals" in app_js
    assert "/research/news" in app_js
    assert "/research/capital-flow" in app_js
    assert "/research/longhubang" in app_js
    assert "/research/unlocks" in app_js
    assert "研究工具调试" in app_js
    assert "研究信号" in app_js
    assert "计划对齐" in app_js
    assert "当前计划方向" in app_js
    assert "主力净流入" in app_js
    assert "龙虎榜净额" in app_js
    assert "净流入" in app_js or "净流出" in app_js
    assert "资金流：" in app_js
    assert "公告：" in app_js


def test_web_styles_define_workbench_layout() -> None:
    css = read_web_file("src/styles.css")

    assert ".workbench-shell" in css
    assert ".filter-row" in css
    assert ".task-history-search" in css
    assert ".filter-chip" in css
    assert ".task-history-card" in css
    assert ".side-panel" in css
    assert ".report-detail" in css
    assert "@media" in css


def test_web_readme_documents_static_open_flow() -> None:
    readme = read_web_file("README.md")

    assert "index.html" in readme
    assert "离线 mock" in readme
    assert "HTTP API" in readme


def test_app_js_exposes_http_service_boundary() -> None:
    app_js = read_web_file("src/app.js")

    assert "function getApiBaseUrl" in app_js
    assert "async function createHttpAnalysis" in app_js
    assert "async function createHttpAnalysisTask" in app_js
    assert "async function pollAnalysisTask" in app_js
    assert "async function cancelHttpAnalysisTask" in app_js
    assert "async function retryHttpAnalysisTask" in app_js
    assert "async function fetchTaskHistory" in app_js
    assert "function renderTaskHistory" in app_js
    assert 'fetch(`${apiBaseUrl}/tasks/analysis`' in app_js
    assert 'fetch(`${apiBaseUrl}/tasks?limit=' in app_js
    assert 'fetch(`${apiBaseUrl}/tasks/' in app_js
    assert "createLocalAnalysis" in app_js
    assert "next_retry_at" in app_js
    assert "next_retry_policy" in app_js
    assert "fallback_reason" in app_js


def test_app_js_exposes_startup_diagnostics_boundary() -> None:
    app_js = read_web_file("src/app.js")

    assert "moneyNeverSleep" in app_js
    assert "startup-diagnostics" in app_js or "启动模式" in app_js
