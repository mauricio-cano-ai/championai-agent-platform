import asyncio

import pytest

from app.domain import IncidentRequest, TaskRecord, TaskStatus
from app.store import InMemoryTaskStore


def run(coro):
    return asyncio.run(coro)


def record(task_id="t-1", request_id="r-1"):
    return TaskRecord(
        task_id=task_id,
        request=IncidentRequest(request_id=request_id, asset_id="line", summary="valid incident summary"),
        status=TaskStatus.INVESTIGATING,
    )


def test_store_returns_none_for_unknown_records_and_reuses_request_id():
    store = InMemoryTaskStore()
    assert run(store.get("missing")) is None
    assert run(store.get_by_request_id("missing")) is None
    first = run(store.create(record()))
    replay = run(store.create(record(task_id="t-2")))
    assert replay.task_id == first.task_id


def test_store_save_requires_existing_task():
    store = InMemoryTaskStore()
    with pytest.raises(KeyError):
        run(store.save(record()))
