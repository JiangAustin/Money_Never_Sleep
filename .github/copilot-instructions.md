# Money Workspace Instructions

- Treat `Money` as the main project. The sibling repositories are references unless the user explicitly asks to edit them.
- Do not copy large blocks of source code from reference projects. Prefer documenting integration points and porting small, reviewed slices when needed.
- Keep configuration portable. Do not hardcode absolute local paths, secrets, model names, ports, or account identifiers.
- Start with narrow vertical slices: API contract, data adapter, analysis workflow, UI surface, then packaging.
- Keep generated data, cache, reports, and local environment files out of version control.
- Local superpowers-zh skills are installed under `.github/superpowers/`. Use the relevant skill instructions there when the task matches a listed workflow, such as brainstorming, planning, TDD, systematic debugging, verification, or code review.
