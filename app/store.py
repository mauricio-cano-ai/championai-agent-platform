from __future__ import annotations

import asyncio

from .domain import TaskRecord


class InMemoryTaskStore:
    """Deterministic test/demo store with atomic idempotency and execution claims.

    Production adapters should provide the same semantics with durable storage.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}
        self._request_index: dict[str, str] = {}
        self._execution_claims: set[str] = set()
        self._lock = asyncio.Lock()

    async def get_by_request_id(self, request_id: str) -> TaskRecord | None:
        async with self._lock:
            task_id = self._request_index.get(request_id)
            task = self._tasks.get(task_id) if task_id else None
            return task.model_copy(deep=True) if task else None

    async def get(self, task_id: str) -> TaskRecord | None:
        async with self._lock:
            task = self._tasks.get(task_id)
            return task.model_copy(deep=True) if task else None

    async def create(self, task: TaskRecord) -> TaskRecord:
        async with self._lock:
            existing_id = self._request_index.get(task.request.request_id)
            if existing_id:
                return self._tasks[existing_id].model_copy(deep=True)
            self._tasks[task.task_id] = task.model_copy(deep=True)
            self._request_index[task.request.request_id] = task.task_id
            return task.model_copy(deep=True)

    async def save(self, task: TaskRecord) -> TaskRecord:
        async with self._lock:
            if task.task_id not in self._tasks:
                raise KeyError(task.task_id)
            self._tasks[task.task_id] = task.model_copy(deep=True)
            return task.model_copy(deep=True)

    async def claim_execution(self, task_id: str) -> bool:
        async with self._lock:
            if task_id in self._execution_claims:
                return False
            self._execution_claims.add(task_id)
            return True
