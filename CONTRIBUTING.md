# Contributing

Keep changes small, typed and testable. Any behavior change should start with a failing test that demonstrates the desired invariant.

Before opening a pull request:

```bash
python -m pip install -e ".[dev]"
python -m ruff check app tests
pyright
coverage run -m pytest
coverage report -m
```

Do not weaken approval, idempotency or execution-claim semantics to make an integration easier. Add transport/provider behavior behind a port instead.
