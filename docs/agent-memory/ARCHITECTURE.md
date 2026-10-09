# Agent Memory and Context Architecture

## Memory layers
1. **Skills** — reusable operating instructions in `.agents/skills/<name>/SKILL.md`. Load by task relevance, not all at once.
2. **Project memory** — durable goals, architecture, decisions and known issues in `docs/agent-memory/`.
3. **Task state** — current execution status and checkpoints in `.tigerdatalab/agent-memory/tasks/<task-id>.json` when using the local `ProjectMemory` helper.
4. **Evidence** — observed test results, CI URLs, commit SHAs and changed paths. Evidence is not interchangeable with an agent's statement that work is done.
5. **Runtime state** — transient state passed through an agent or workflow; it should not automatically become long-term memory.

## Lifecycle
Load relevant skills and project context → inspect current implementation → define acceptance criteria → execute bounded steps → verify with tests/CI → record factual evidence → summarize outcome.

## Context selection
Use `SkillLoader.list_skills()` to discover available skills and `SkillLoader.load([...])` to load only the selected set. Do not silently load every skill. Keep large artifacts outside prompts and retrieve only the sections needed.

## Safety and durability
`ProjectMemory` writes JSON atomically, bounds document size, validates task identifiers, and rejects credential-shaped keys. It is a local single-process helper, not a multi-tenant database or encrypted secret store. Use a database and access controls for hosted multi-user deployments.

## Current boundary
This foundation adds selective skill loading and bounded local project/task memory. It does not yet provide automatic context ranking, a distributed checkpoint store, or a durable graph scheduler.
