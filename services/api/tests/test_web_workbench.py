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
        "data_context",
    ):
        assert field in mock_data

    assert "window.MNS_MOCK_REPORTS" in mock_data


def test_app_js_exposes_service_and_render_boundaries() -> None:
    app_js = read_web_file("src/app.js")

    assert "function createLocalAnalysis" in app_js
    assert "function renderReportList" in app_js
    assert "function renderReportDetail" in app_js
    assert "function renderDiagnostics" in app_js
    assert "analysis-form" in app_js


def test_web_styles_define_workbench_layout() -> None:
    css = read_web_file("src/styles.css")

    assert ".workbench-shell" in css
    assert ".side-panel" in css
    assert ".report-detail" in css
    assert "@media" in css


def test_web_readme_documents_static_open_flow() -> None:
    readme = read_web_file("README.md")

    assert "index.html" in readme
    assert "离线 mock" in readme
    assert "HTTP API" in readme
