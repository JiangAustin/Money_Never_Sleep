# Money

Money is a finance and stock analysis workspace that will integrate ideas from three reference projects:

- `TradingAgents-astock`: multi-agent A-share research workflow.
- `go-stock`: desktop application and local data/application packaging patterns.
- `daily_stock_analysis`: Python service layering, API, reports, Web, and Desktop boundaries.

This first scaffold intentionally defines project boundaries before copying or porting implementation code.

## Project Layout

```text
Money/
  apps/
    web/              # Web client shell
    desktop/          # Desktop client shell
  services/
    api/              # Python API service
  packages/
    shared/           # Shared contracts and generated clients
  data/
    raw/              # Unmodified local input data
    processed/        # Derived local datasets
    cache/            # Runtime cache, safe to recreate
  docs/               # Architecture, references, roadmap
  scripts/            # Local developer scripts
```

## First Milestone

1. Keep reference projects external and document their integration points.
2. Build a minimal API service boundary under `services/api`.
3. Decide whether the desktop shell should be Wails, Electron, or another wrapper after the product workflow is clearer.
4. Add real dependencies only when a concrete feature slice needs them.
