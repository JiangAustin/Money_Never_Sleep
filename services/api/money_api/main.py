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


if __name__ == "__main__":
    print(health())
