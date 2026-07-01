---
name: mns-stage-delivery
description: Use when a Money_Never_sleep task is a stage, backlog slice, second-version feature, or multi-step change that must preserve repo memory, validation evidence, and commit outlines.
version: "1.0.0"
---

# MNS Stage Delivery

## Overview

Use this project skill to keep Money_Never_sleep stage work consistent: narrow slice, documented design, test-first implementation, durable handoff, validation, commit outline, and cleanup.

## When To Use

Use for:

- A numbered stage or backlog item from `docs/stages.md` or `docs/improvement-backlog.md`.
- A second-version feature that changes API, Web/Desktop workflow, data providers, analysis behavior, validation commands, or project rules.
- A task that will need future agents to understand what changed and why.

Do not use for tiny typo fixes, one-off questions, or read-only review.

## Required Flow

1. Read `README.md`, `docs/stages.md`, `docs/information-map.md`, `docs/improvement-backlog.md`, and `docs/agent-handoff.md` only as far as needed for the slice.
2. If the task changes behavior, write or update a short spec in `docs/superpowers/specs/` and an implementation plan in `docs/superpowers/plans/`.
3. Work in a branch or worktree for feature slices; keep generated data, caches, reports, `node_modules`, and build output out of commits.
4. Use TDD where practical: add or update the closest failing test before implementation, then make the smallest implementation that passes.
5. Update durable docs before closing the slice:
   - `README.md` when user-visible capabilities, setup, API entrypoints, Web/Desktop workflows, packaging, or architecture direction changed.
   - `docs/stages.md` for stage status, validation, and next recommendation.
   - `docs/improvement-backlog.md` for deferred work, completed backlog items, and known limits.
   - `docs/agent-handoff.md` for what changed, why, benefits, remaining gaps, validation evidence, and recommended next move.
   - `docs/information-map.md` when new important entrypoints or write-back rules were added.
6. Validate with the narrowest relevant command first, then run the repo-level checks for the touched area. Build the macOS desktop app after completed coding slices unless clearly irrelevant or unavailable.
7. Commit each completed slice with a concise subject and an outline-style commit body.
8. After merge/push, clean temporary worktrees and confirm `git rev-list --left-right --count <branch>...origin/<branch>` is `0 0`.

## Validation Defaults

Backend/API:

```bash
PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -q
```

Web/Desktop syntax:

```bash
node --check apps/web/src/app.js && node --check apps/web/src/mockData.js && node --check apps/desktop/src/main.js && node --check apps/desktop/src/preload.js
```

Desktop macOS build:

```bash
cd apps/desktop && npm audit --audit-level=high && npm run build:mac
```

## Common Mistakes

- Leaving stage status as `进行中` after code is merged.
- Recording deferred work only in chat or commit messages instead of `docs/improvement-backlog.md`.
- Forgetting `docs/agent-handoff.md` after changing architecture or validation commands.
- Claiming a network or external-engine path is verified without an opt-in smoke command and captured result.
- Committing generated build output or local cache files.
