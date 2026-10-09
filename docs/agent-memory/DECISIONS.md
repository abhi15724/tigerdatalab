# Architecture Decisions

## 2026-10-09 — Keep data and agents as equal pillars
Decision: TigerDataLab remains both a data engineering/training toolkit and an agent framework. Agent features must reuse data quality, lineage, privacy and evaluation capabilities rather than replace them.

## 2026-10-09 — Skills are selective instructions, not hidden state
Decision: Store reusable workflow guidance as readable `SKILL.md` files and load only the relevant skills for each task.

## 2026-10-09 — Separate memory from execution evidence
Decision: Project notes, current task state, runtime state and observed evidence are separate concepts. Completion claims require actual test/CI or other relevant evidence.

## 2026-10-09 — Local JSON memory is a starter, not a hosted store
Decision: The initial helper is bounded, atomic and local. Multi-user services require access control, tenant isolation, retention policies and a durable backend.

## 2026-10-09 — Token efficiency must preserve quality
Decision: Optimize cost per successful task, not raw token count. Essential verification and safety checks are not optional cost savings.
