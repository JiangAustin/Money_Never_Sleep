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
