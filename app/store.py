from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from copy import deepcopy

from app.domain import TaskView


class TaskStore(ABC):
    @abstractmethod
    async def get_by_idempotency_key(self, key: str) -> TaskView | None: ...

    @abstractmethod
    async def save(self, task: TaskView) -> TaskView: ...

    @abstractmethod
    async def get(self, task_id: str) -> TaskView | None: ...

    @abstractmethod
    async def claim_action(self, action_id: str) -> bool:
        """Return True only for the first caller that claims this side effect."""


class InMemoryTaskStore(TaskStore):
    def __init__(self) -> None:
        self.tasks: dict[str, TaskView] = {}
        self.by_key: dict[str, str] = {}
        self.claimed_actions: set[str] = set()
        self._lock = asyncio.Lock()

    async def get_by_idempotency_key(self, key: str) -> TaskView | None:
        async with self._lock:
            task_id = self.by_key.get(key)
            return deepcopy(self.tasks.get(task_id)) if task_id else None

    async def save(self, task: TaskView) -> TaskView:
        async with self._lock:
            self.tasks[task.id] = deepcopy(task)
            self.by_key[task.idempotency_key] = task.id
            return deepcopy(task)

    async def get(self, task_id: str) -> TaskView | None:
        async with self._lock:
            task = self.tasks.get(task_id)
            return deepcopy(task) if task else None

    async def claim_action(self, action_id: str) -> bool:
        async with self._lock:
            if action_id in self.claimed_actions:
                return False
            self.claimed_actions.add(action_id)
            return True
