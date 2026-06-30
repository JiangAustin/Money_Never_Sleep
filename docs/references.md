# Reference Projects

The current workspace includes three sibling projects used as references:

| Project | Role in Money |
| --- | --- |
| `TradingAgents-astock` | Multi-agent A-share analysis, ticker normalization, market data workflows |
| `go-stock` | Go/Wails desktop packaging, local app structure, stock data UI ideas |
| `daily_stock_analysis` | FastAPI/API layering, data provider fallback, report generation, Web/Desktop split |

Initial rule: use these projects for architecture and integration guidance. Do not vendor their source into Money until a specific feature requires a reviewed port.
