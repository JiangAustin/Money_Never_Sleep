# Roadmap

## Step 1: Workspace Shape

- Define project boundaries.
- Keep reference projects external.
- Add minimal API package and test boundary.

## Step 2: First Vertical Slice

- Build the backend contract for a single-stock deep analysis loop.
- Keep the first slice deterministic with offline fixtures and a mock deep research engine.
- Add TradingAgents-astock integration only after the platform contract and report schema are tested.

## Step 3: Integration Choice

- Decide which reference project behavior to port first.
- Add only the dependencies needed by that slice.
- Document compatibility and validation paths.
