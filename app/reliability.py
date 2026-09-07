from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def retry_async(
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    base_delay_s: float = 0.05,
    jitter_s: float = 0.02,
) -> T:
    """Retry transient async work with bounded exponential backoff + jitter."""
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return await fn()
        except (TimeoutError, ConnectionError) as exc:
            last_error = exc
            if attempt == attempts - 1:
                break
            delay = base_delay_s * (2**attempt) + random.random() * jitter_s
            await asyncio.sleep(delay)
    assert last_error is not None
    raise last_error
