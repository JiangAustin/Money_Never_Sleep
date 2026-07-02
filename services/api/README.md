# Money_Never_sleep API Service

This service owns backend APIs, orchestration, data adapters, and analysis workflows for the Money_Never_sleep project.

Current state: analysis contracts, task queue, market-data adapters, structured event extraction, report provenance, backtest, and portfolio budget services are implemented behind a dependency-free JSON HTTP boundary. The runtime market-data bundle now prefers live Tencent quote, Sina technicals, Eastmoney F10 fundamentals, optional iWenCai, and a tool-driven fallback path when TradingAgents is unavailable.
