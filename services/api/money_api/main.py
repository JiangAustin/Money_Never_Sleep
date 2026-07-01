"""Minimal API application boundary for the Money_Never_sleep workspace."""


def health() -> dict[str, str]:
    """Return a minimal health payload for early scaffolding checks."""
    return {"status": "ok", "service": "money-never-sleep-api"}


def analyze_stock(symbol: str, message: str) -> dict[str, object]:
    from money_api.api.v1.router import analyze_stock as analyze_stock_v1

    return analyze_stock_v1(symbol, message)


def get_analysis_report(task_id: str) -> dict[str, object] | None:
    from money_api.api.v1.router import get_analysis_report as get_analysis_report_v1

    return get_analysis_report_v1(task_id)


def list_analysis_reports(limit: int = 20) -> list[dict[str, object]]:
    from money_api.api.v1.router import list_analysis_reports as list_analysis_reports_v1

    return list_analysis_reports_v1(limit=limit)


def backtest_analysis_report(
    task_id: str,
    prices: list[dict[str, object]] | None = None,
    source: str | None = None,
    limit: int = 60,
    options: dict[str, object] | None = None,
) -> dict[str, object] | None:
    from money_api.api.v1.router import backtest_analysis_report as backtest_analysis_report_v1

    return backtest_analysis_report_v1(task_id=task_id, prices=prices, source=source, limit=limit, options=options)


def build_portfolio_risk_budget(task_ids: list[str] | None = None, limit: int = 20) -> dict[str, object]:
    from money_api.api.v1.router import build_portfolio_risk_budget as build_portfolio_risk_budget_v1

    return build_portfolio_risk_budget_v1(task_ids=task_ids, limit=limit)


def run_http_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    from money_api.api.http import run_http_server as run_http_server_v1

    return run_http_server_v1(host=host, port=port)


if __name__ == "__main__":
    print(health())
