# ADR 0001: Keep execution authority deterministic

**Status:** Accepted

## Decision

Agent reasoning may generate evidence and proposals, but authorization and side-effect ownership remain deterministic software state. Every external action requires an explicit human approval plus an atomic execution claim.

## Consequences

This adds a state machine and persistence requirement, but makes duplicate approvals, retries and model variability safe to reason about. Model quality can improve independently without changing the authorization model.
