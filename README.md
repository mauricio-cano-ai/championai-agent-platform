# ChampionAI Agent Platform

**Runnable Python reference architecture for agentic systems with a real MCP v2 evidence gateway, while keeping authority, side effects and human approval deterministic.**

This repository is an engineering lab, not a claim that the manufacturing scenario is deployed in production. Its purpose is to make software-engineering decisions reviewable: typed contracts, idempotent task intake, bounded retries, explicit approval gates, atomic execution claims, deterministic tests and observable API boundaries.

## What a reviewer can verify in 5 minutes

```text
POST /v1/incidents
      â”‚
      â–¼
 idempotent request key â”€â”€â–º Planner â”€â”€â–º Investigator
      â”‚                         â”‚              â”‚
      â”‚                         â””â”€â”€â”€â”€ evidenceâ”˜
      â–¼
WAITING_APPROVAL  â—„â”€â”€ typed action proposal
      â”‚
      â”œâ”€â”€ reject â”€â”€â–º REJECTED
      â”‚
      â””â”€â”€ approve â”€â–º atomic execution claim â”€â–º Executor â”€â–º COMPLETED
```

| Engineering concern | Evidence in this repo |
|---|---|
| Typed Python API | FastAPI + Pydantic contracts in `app/api.py` and `app/domain.py` |
| Orchestration | Planner â†’ Investigator â†’ proposal â†’ approval â†’ executor in `app/orchestrator.py` |
| Human-in-the-loop | Side effects are impossible before explicit approval |
| Idempotency | Request-id index and atomic execution claim in `app/store.py` |
| Reliability | Bounded retry policy only for transient failures in `app/reliability.py` |
| Quality gates | pytest + branch coverage â‰¥90%, Ruff, Pyright strict, Docker build in CI |
| Observability | Structured JSON event helper; health/readiness endpoints |
| Interoperability | Transport-independent MCP/A2A contract examples under `examples/` |
| AI quality | Deterministic software tests separated from optional behavioral evals under `evals/` |

## Why the boundaries matter

An LLM or agent may propose what to do. It does **not** own authorization, idempotency or the right to create external side effects. Those are ordinary software invariants and remain deterministic. The core rule is:

> **model reasoning may be probabilistic; execution authority may not be.**

That is why approval and duplicate-action protection live outside the agent implementation.

## Run locally

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
make verify
uvicorn app.api:app --reload
```

Open `http://127.0.0.1:8000/docs` for the generated OpenAPI UI.

Example:

```bash
curl -X POST http://127.0.0.1:8000/v1/incidents \
  -H "content-type: application/json" \
  -d '{"request_id":"demo-001","asset_id":"line-4","summary":"Temperature excursion after a configuration change"}'
```

The response stops at `WAITING_APPROVAL`; the executor has not run.

## Verification

```bash
python -m pytest
coverage run -m pytest && coverage report -m
python -m ruff check app tests
pyright
docker build -t championai-agent-platform .
```

CI runs the same deterministic checks on Python 3.11 and 3.12, plus a container build. CodeQL and Dependabot are configured separately.

## MCP v2 interoperability

ChampionAI includes a real MCP v2 evidence gateway implemented with the official Model Context Protocol Python SDK.

The server in `app/mcp_server.py` exposes typed, read-only tools for incident context, asset context, and safety constraints. The protocol smoke test in `tests/test_mcp_v2_smoke.py` connects with the official MCP client in-process, discovers the tools, and verifies typed input schemas and unique tool names.

MCP is intentionally an interoperability boundary, not an authority layer. Human approval, authorization, idempotency, execution claims, and mutating side effects remain deterministic application responsibilities.

Reviewer smoke test:

    python -m pytest tests/test_mcp_v2_smoke.py -q

A2A remains represented separately by the transport-independent boundary example under `examples/`.
## Behavioral evaluation

`pytest` validates invariants. Model-behavior evaluation belongs under `evals/` and is opt-in because live-provider tests can be non-deterministic, network-dependent and billable. There are deliberately no fabricated eval scores in this repository.

## Architecture & operating docs

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/FAILURE_MODES.md`](docs/FAILURE_MODES.md)
- [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md)
- [`docs/adr/0001-deterministic-authority-boundary.md`](docs/adr/0001-deterministic-authority-boundary.md)
- [`docs/adr/0002-separate-evals-from-deterministic-ci.md`](docs/adr/0002-separate-evals-from-deterministic-ci.md)
- [`SECURITY.md`](SECURITY.md)
- [`CONTRIBUTING.md`](CONTRIBUTING.md)

## Related production evidence

This lab complements two separate repositories:

- **EasyAIgent Agentic Systems Portfolio** â€” sanitized patterns from a real multitenant AI-enabled CRM/operations platform.
- **AWS Bedrock Production Integration** â€” sanitized, reproducible counterpart of a live EasyAIgent path deployed with API Gateway, Lambda, Bedrock Nova, DynamoDB, IAM/SSM and CloudWatch/X-Ray.

â€” **Mauricio Alfonso Cano** Â· [GitHub](https://github.com/mauricio-cano-ai) Â· [LinkedIn](https://www.linkedin.com/in/mauricio-alfonso-cano-ai/)
