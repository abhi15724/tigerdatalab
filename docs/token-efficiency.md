# Token-Efficient Agent Design

TigerDataLab should minimize **cost per successfully completed task**, while maintaining correctness and safety.

## Practical rules
- Retrieve only the relevant skills and source files.
- Carry compact structured state between steps rather than replaying full history.
- Keep tool results concise; fetch full logs only for failures or ambiguous outcomes.
- Route routine tasks to lower-cost capable models and escalate difficult tasks when needed.
- Cache deterministic outputs only when cache keys include all relevant inputs and stale data is acceptable.
- Track actual usage from provider telemetry when available; mark heuristic estimates as estimates.
- Use bounded retries and repair only the failed stage.
- Stop cleanly when a budget is exhausted and return partial state/evidence.
- Preserve essential testing, privacy, authorization and approval checks.

## Metrics
Measure tokens per successful task, cost per successful task, task success rate, evaluation quality, latency, retry count and recovery rate. Compare systems on the same workload and quality threshold.
