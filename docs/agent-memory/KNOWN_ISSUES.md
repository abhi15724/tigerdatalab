# Known Issues and Boundaries

- Current `Workflow` executes a list of steps in order; conditional steps exist, but graph routing, durable checkpoints and parallel execution are not implemented here.
- `ProjectMemory` is local JSON persistence and is not safe to share across untrusted tenants without additional controls.
- `SkillLoader` loads plain UTF-8 Markdown files; it does not execute skill content.
- Credential detection checks field names and is not a substitute for secret scanning or access control.
- Provider token usage is not guaranteed to be present or normalized across all adapters.
- CI and full-suite results must be checked from actual Actions runs before release.
