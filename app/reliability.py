from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.2
    max_delay_seconds: float = 2.0


def _retryable(exc: Exception) -> bool:
    return isinstance(exc, (TimeoutError, ConnectionError))


async def retry_async(operation: Callable[[], Awaitable[T]], policy: RetryPolicy) -> T:
    if policy.max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return await operation()
        except Exception as exc:
            if not _retryable(exc) or attempt == policy.max_attempts:
                raise
            delay = min(policy.max_delay_seconds, policy.base_delay_seconds * (2 ** (attempt - 1)))
            if delay > 0:
                await asyncio.sleep(delay)
    raise RuntimeError("unreachable")
