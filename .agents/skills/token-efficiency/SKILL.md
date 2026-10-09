# Token Efficiency

## Objective
Minimize total tokens and cost per successfully completed task while preserving correctness, security and verification. Fewer tokens is not a win if the result becomes unreliable.

## Workflow
1. Identify the task and acceptance criteria in a short structured plan.
2. Load only relevant skill files and targeted source ranges; do not dump the whole repository into context.
3. Reuse project memory and verified evidence, checking dates/commit hashes before relying on it.
4. Ask tools for compact structured outputs; inspect full logs only when a failure or ambiguity requires them.
5. Use the smallest capable model for routine transformations and reserve stronger models for ambiguous design, high-risk review or difficult debugging.
6. Cache deterministic results where safe; never cache secrets or user-specific sensitive data in shared scope.
7. Pass compact state and evidence between graph nodes instead of repeating conversation history.
8. Retry only the failed part; cap retries and stop when the quality threshold or budget is reached.
9. Measure actual input/output tokens, latency, cost and task quality when provider telemetry is available. Label estimates as estimates.
10. Keep final reports concise but include changes, tests, failures and next action.

Never bypass permission checks, privacy safeguards, essential tests or user approval to reduce token usage.
