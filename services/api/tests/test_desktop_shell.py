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
    assert {"from": "../../services/api", "to": "services-api", "filter": ["**/*"]} in extra_resources


def test_desktop_main_loads_web_workbench() -> None:
    main_js = (DESKTOP_ROOT / "src/main.js").read_text(encoding="utf-8")

    assert "BrowserWindow" in main_js
    assert "index.html" in main_js
    assert "MNS_DESKTOP_API_URL" in main_js
    assert "process.resourcesPath" in main_js
    assert "MNS_DESKTOP_PYTHON_BIN" in main_js
    assert "spawn(" in main_js
    assert "/health" in main_js
    assert "PYTHONPATH" in main_js
    assert "before-quit" in main_js
    assert "additionalArguments" in main_js
    assert "--mns-startup=" in main_js


def test_desktop_preload_exposes_versions() -> None:
    preload_js = (DESKTOP_ROOT / "src/preload.js").read_text(encoding="utf-8")

    assert "contextBridge" in preload_js
    assert "moneyNeverSleep" in preload_js
    assert "startup" in preload_js
    assert "--mns-startup=" in preload_js
