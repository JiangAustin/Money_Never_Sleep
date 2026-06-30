# Architecture

Money_Never_sleep starts as a modular finance analysis workspace with explicit boundaries:

- API service: backend contracts, orchestration, analysis workflows, provider adapters.
- Web app: browser-based research and portfolio workflows.
- Desktop app: local packaging and OS-specific capabilities.
- Shared package: schemas and generated clients when cross-app contracts stabilize.
- Data directories: local raw, processed, and cache files that can be recreated or ignored safely.

The first implementation slices should stay small and prove one end-to-end workflow before expanding the module surface.
