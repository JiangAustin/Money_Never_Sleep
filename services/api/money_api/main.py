"""Minimal API application boundary for the Money workspace."""


def health() -> dict[str, str]:
    """Return a minimal health payload for early scaffolding checks."""
    return {"status": "ok", "service": "money-api"}


if __name__ == "__main__":
    print(health())
