# Failure modes

| Failure | Unsafe implementation | Repository boundary |
|---|---|---|
| Duplicate intake | Starts two agent runs | `request_id` returns the same logical task |
| Approval replay | Repeats external action | `claim_execution()` allows one owner |
| Model timeout | Infinite/unbounded retries | bounded retry budget for transient errors only |
| Invalid model/tool contract | Guess at missing fields | typed Pydantic contracts fail closed |
| Human rejects proposal | Agent continues anyway | terminal `REJECTED` state |
| Transport outage | Orchestration tied to MCP/A2A SDK | ports keep transport behind an adapter |
| Eval provider unavailable | CI becomes flaky | live behavioral evals separated from deterministic CI |
| Sensitive payload in logs | Customer data leakage | structured events should log IDs/state, not payload bodies |

A production implementation should add durable transactional storage, distributed tracing and provider-specific timeouts while preserving these invariants.
