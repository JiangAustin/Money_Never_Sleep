import json
from pathlib import Path


DESKTOP_ROOT = Path("apps/desktop")


def read_package() -> dict:
    return json.loads((DESKTOP_ROOT / "package.json").read_text(encoding="utf-8"))


def test_desktop_package_has_electron_scripts() -> None:
    package = read_package()

    assert package["main"] == "src/main.js"
    assert package["scripts"]["start"] == "electron ."
    assert package["scripts"]["build:mac"] == "electron-builder --mac dir"


def test_desktop_package_includes_web_resources() -> None:
    package = read_package()
    extra_resources = package["build"]["extraResources"]

    assert {"from": "../web", "to": "web", "filter": ["**/*"]} in extra_resources
