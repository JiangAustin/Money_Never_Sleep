"""Configuration placeholders for the Money_Never_sleep API service."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    env: str = os.getenv("MONEY_ENV", "development")
    api_host: str = os.getenv("MONEY_API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("MONEY_API_PORT", "8000"))
    analysis_reports_dir: str = os.getenv("MONEY_REPORTS_DIR", "data/cache/reports")
    analysis_tasks_dir: str = os.getenv("MONEY_TASKS_DIR", "data/cache/tasks")
    tradingagents_astock_path: str = os.getenv("TRADINGAGENTS_ASTOCK_PATH", "../TradingAgents-astock")
    tradingagents_results_dir: str = os.getenv("TRADINGAGENTS_RESULTS_DIR", "data/cache/tradingagents/results")
    tradingagents_cache_dir: str = os.getenv("TRADINGAGENTS_CACHE_DIR", "data/cache/tradingagents/cache")


settings = Settings()
