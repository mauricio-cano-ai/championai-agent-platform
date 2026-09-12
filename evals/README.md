# Behavioral evaluations

Deterministic CI and behavioral model evaluation are deliberately separated.

- `pytest` proves software invariants: idempotency, approval gates, state transitions, retry boundaries and API contracts.
- Model-facing evaluation belongs here and is opt-in (`pip install -e ".[eval]"`) because it may require a provider key, network access and variable cost.
- A model eval must never replace deterministic tests for permissions, authority or side effects.

The public repository intentionally does not ship a fake score or a CI badge implying live-provider evaluation on every commit.
