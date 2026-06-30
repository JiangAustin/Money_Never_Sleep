from money_api.main import analyze_stock, get_analysis_report, health


def test_analyze_stock_api_returns_serialized_report() -> None:
    payload = analyze_stock("贵州茅台", "请全面分析并给出投资建议")

    assert payload["stock"]["code"] == "600519"
    assert payload["status"] == "report_ready"
    assert payload["summary"]
    assert payload["agent_views"]

    loaded = get_analysis_report(payload["task_id"])
    assert loaded == payload


def test_get_analysis_report_returns_none_for_missing_task() -> None:
    assert get_analysis_report("missing-task") is None


def test_health_api_still_returns_original_payload() -> None:
    assert health() == {"status": "ok", "service": "money-never-sleep-api"}