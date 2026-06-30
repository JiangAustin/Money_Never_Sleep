"""Version 1 route placeholders."""

from money_api.main import health


def routes() -> dict[str, object]:
    return {"health": health()}
