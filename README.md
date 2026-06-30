# Money_Never_sleep

Money_Never_sleep is a finance and stock analysis workspace that will integrate ideas from three reference projects:

- `TradingAgents-astock`: multi-agent A-share research workflow.
- `go-stock`: desktop application and local data/application packaging patterns.
- `daily_stock_analysis`: Python service layering, API, reports, Web, and Desktop boundaries.

This first scaffold intentionally defines project boundaries before copying or porting implementation code.

## Project Layout

```text
Money_Never_sleep/
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

## Current Planning Slice

The first implementation slice is the backend contract for a single-stock deep analysis loop:

1. Resolve an A-share symbol or Chinese stock name.
2. Build a normalized data context with explicit data gaps.
3. Route quick questions separately from deep analysis requests.
4. Generate a structured dry-run report through an Agent engine adapter.
5. Expose Python-level API functions for tests and early integration.
