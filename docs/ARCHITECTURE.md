# Architecture

## Invariants first

ChampionAI is organized around four invariants:

1. A caller-selected `request_id` identifies one logical incident submission.
2. Investigation may be probabilistic, but it cannot perform side effects.
3. A side effect requires a human decision **and** an atomic execution claim.
4. Replays return existing state instead of duplicating work.

## Components

`IncidentRequest` and `TaskRecord` are typed domain contracts. `Orchestrator` owns state transitions and depends only on four ports: `TaskStore`, `Planner`, `Investigator`, and `Executor`. The in-memory adapters make deterministic testing cheap; a durable adapter can replace the store without changing orchestration semantics.

The HTTP layer is deliberately thin. FastAPI validates external input and maps transition errors to HTTP status codes. It does not own orchestration policy.

## State machine

```text
                    ┌──────────────────┐
request_id ───────► │ INVESTIGATING    │
                    └────────┬─────────┘
                             │ evidence + proposal
                             ▼
                    ┌──────────────────┐
                    │ WAITING_APPROVAL │
                    └──────┬───────┬───┘
                           │       │
                     reject│       │approve + atomic claim
                           ▼       ▼
                    REJECTED      COMPLETED
```

There is no transition from `INVESTIGATING` directly to a side effect.

## Production adapter expectations

A durable `TaskStore` should implement the same semantics with transactions/conditional writes. `claim_execution(task_id)` is the key safety boundary: exactly one actor may acquire execution authority for a task. External model/tool calls should have bounded timeouts and retry only failure classes that are safe to replay.

## Observability

Logs should carry identifiers and state transitions, not raw prompts, secrets or customer payloads. Health endpoints remain dependency-light; a production readiness endpoint can additionally check required durable dependencies when that check is operationally useful.
