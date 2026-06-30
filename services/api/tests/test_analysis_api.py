from money_api.api.v1.router import build_default_analysis_service, build_tencent_quote_analysis_service
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


def test_default_analysis_service_stays_offline() -> None:
    payload = build_default_analysis_service().create_single_stock_analysis("贵州茅台", "请全面分析").to_dict()

    assert payload["stock"]["code"] == "600519"
    assert payload["data_diagnostics"][0]["source"] == "static"


def test_tencent_quote_service_factory_accepts_transport() -> None:
    def transport(url: str) -> str:
        values = [""] * 53
        values[1] = "贵州茅台"
        values[3] = "1688.00"
        return 'v_sh600519="' + "~".join(values) + '";'

    service = build_tencent_quote_analysis_service(transport=transport)
    payload = service.create_single_stock_analysis("贵州茅台", "请全面分析").to_dict()

    assert payload["data_diagnostics"][0]["source"] == "tencent"