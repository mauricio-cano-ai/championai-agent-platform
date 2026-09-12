# ADR 0002: Separate behavioral evals from deterministic CI

**Status:** Accepted

## Decision

Tests for permissions, state transitions, idempotency and retries run on every commit without a model provider. Live/model behavioral evals are opt-in and reported separately.

## Consequences

Pull requests are reproducible and inexpensive. Model-evaluation results remain useful evidence without becoming a substitute for software correctness.
