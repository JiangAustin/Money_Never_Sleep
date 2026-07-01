# Money_Never_sleep Workspace Instructions

- Treat `Money_Never_sleep` as the main project. The sibling repositories are references unless the user explicitly asks to edit them.
- Do not copy large blocks of source code from reference projects. Prefer documenting integration points and porting small, reviewed slices when needed.
- Keep configuration portable. Do not hardcode absolute local paths, secrets, model names, ports, or account identifiers.
- Start with narrow vertical slices: API contract, data adapter, analysis workflow, UI surface, then packaging.
- Keep generated data, cache, reports, and local environment files out of version control.
- Update `README.md` when a completed stage changes project positioning, user-visible capabilities, setup/usage commands, API entrypoints, Web/Desktop workflows, packaging, or major architecture direction.
- Keep `README.md` default-facing content in Chinese. When English is useful, provide an English option such as a linked English document or clearly separated English section, while preserving Chinese as the default entry.
- Maintain `docs/information-map.md` as the navigation guide for future agents. It must explain where to find project positioning, design rationale, plans, implementation details, validation commands, known gaps, and where to write new information after each task.
- Maintain `docs/improvement-backlog.md` as the single place for first-version gaps, deferred work, known limitations, and improvement ideas. Whenever a feature is intentionally deferred or a limitation is discovered, record what was deferred, why it was deferred, the benefit of finishing it, and the recommended next step.
- Maintain `docs/agent-handoff.md` as the durable context handoff for future agents or model changes. After completing a stage or changing architecture, update what was done, why it was done, the benefit, what remains undone, validation evidence, and the recommended next move.
- Local superpowers-zh skills are installed under `.github/superpowers/`. Use the relevant skill instructions there when the task matches a listed workflow, such as brainstorming, planning, TDD, systematic debugging, verification, or code review.
- The agent may proactively use any relevant skills when they help the current goal. For example, before starting stage 2 "真实 A 股数据层", use brainstorming to refine the design and writing-plans to create the implementation plan. Still obey each skill's approval gates and repository safety rules.
- When repeated work reveals a reusable workflow or technique, record it instead of leaving it only in chat. If it is project-specific, add or update a concise skill under `.github/superpowers/`; if it is only a repo rule, update this file or the relevant docs. Future agents should automatically check and use these local skills when a task matches their descriptions.
- For Money_Never_sleep stage, backlog, or second-version feature delivery, use `.github/superpowers/mns-stage-delivery/SKILL.md` to keep specs, plans, tests, validation, docs, commit outlines, and cleanup consistent.
