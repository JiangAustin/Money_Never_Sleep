from money_api.main import health


def test_health_payload() -> None:
    assert health() == {"status": "ok", "service": "money-api"}
