"""Helpers for carrying analysis provenance through reports and UI."""

from __future__ import annotations

from typing import Any


def collect_data_sources(diagnostics: list[dict[str, Any]]) -> list[str]:
    sources: list[str] = []
    for diagnostic in diagnostics:
        source = str(diagnostic.get("source", "")).strip()
        if source and source not in sources:
            sources.append(source)
    return sources


def infer_engine_source(engine_source: str | None, data_sources: list[str]) -> str:
    source = str(engine_source or "").strip()
    if source:
        return source
    for candidate in reversed(data_sources):
        if candidate:
            return candidate
    return "mock"


def infer_engine_mode(engine_mode: str | None, engine_source: str | None = None) -> str:
    mode = str(engine_mode or "").strip()
    if mode:
        return mode

    source = str(engine_source or "").strip()
    if source == "mock-fallback":
        return "auto"
    if source == "quick-agent":
        return "quick-screening"
    if "tradingagents" in source:
        return "tradingagents"
    if source:
        return source
    return "mock"
