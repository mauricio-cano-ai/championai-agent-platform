import asyncio

import pytest

from app.reliability import RetryPolicy, retry_async


def test_retry_async_recovers_from_transient_timeout():
    attempts = 0

    async def flaky():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise TimeoutError("temporary")
        return "ok"

    result = asyncio.run(retry_async(flaky, RetryPolicy(max_attempts=3, base_delay_seconds=0)))
    assert result == "ok"
    assert attempts == 3


def test_retry_async_does_not_retry_programming_errors():
    attempts = 0

    async def broken():
        nonlocal attempts
        attempts += 1
        raise ValueError("bad contract")

    with pytest.raises(ValueError, match="bad contract"):
        asyncio.run(retry_async(broken, RetryPolicy(max_attempts=3, base_delay_seconds=0)))
    assert attempts == 1


def test_retry_policy_rejects_zero_attempts_at_runtime_boundary():
    async def ok():
        return "ok"
    with pytest.raises(ValueError, match="max_attempts"):
        asyncio.run(retry_async(ok, RetryPolicy(max_attempts=0)))


def test_retry_async_raises_last_timeout_after_budget_is_exhausted():
    attempts = 0
    async def always_timeout():
        nonlocal attempts
        attempts += 1
        raise TimeoutError("still down")
    with pytest.raises(TimeoutError, match="still down"):
        asyncio.run(retry_async(always_timeout, RetryPolicy(max_attempts=2, base_delay_seconds=0)))
    assert attempts == 2
