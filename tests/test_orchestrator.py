import asyncio

import pytest

from app.domain import IncidentRequest, TaskRecord, TaskStatus
from app.orchestrator import Orchestrator
from app.store import InMemoryTaskStore


class Planner:
    async def plan(self, request):
        return ["inspect telemetry", "check recent changes"]


class Investigator:
    async def collect(self, request, plan):
        return [
            {"source": "telemetry", "summary": "temperature high", "confidence": 0.91},
            {"source": "change_log", "summary": "cooling profile changed", "confidence": 0.82},
        ]


class Executor:
    def __init__(self):
        self.calls = 0

    async def execute(self, proposal):
        self.calls += 1
        return {"action_id": f"act-{self.calls}", "status": "accepted"}


def run(coro):
    return asyncio.run(coro)


def make_system():
    executor = Executor()
    system = Orchestrator(
        store=InMemoryTaskStore(),
        planner=Planner(),
        investigator=Investigator(),
        executor=executor,
    )
    return system, executor


def test_submit_is_idempotent_and_stops_at_human_approval_boundary():
    system, executor = make_system()
    request = IncidentRequest(
        request_id="incident-001",
        asset_id="line-4",
        summary="Temperature excursion after configuration change",
    )

    first = run(system.submit(request))
    replay = run(system.submit(request))

    assert first.task_id == replay.task_id
    assert first.status is TaskStatus.WAITING_APPROVAL
    assert len(first.evidence) == 2
    assert first.proposal is not None
    assert executor.calls == 0


def test_approval_executes_side_effect_exactly_once_even_when_replayed():
    system, executor = make_system()
    task = run(system.submit(IncidentRequest(
        request_id="incident-002",
        asset_id="line-9",
        summary="Unexpected vibration pattern",
    )))

    first = run(system.approve(task.task_id, approved_by="ops@example.com"))
    replay = run(system.approve(task.task_id, approved_by="ops@example.com"))

    assert first.status is TaskStatus.COMPLETED
    assert replay.status is TaskStatus.COMPLETED
    assert first.execution == replay.execution
    assert executor.calls == 1


def test_rejection_is_terminal_and_never_executes_side_effect():
    system, executor = make_system()
    task = run(system.submit(IncidentRequest(
        request_id="incident-003",
        asset_id="line-2",
        summary="Sensor drift suspected",
    )))

    rejected = run(
        system.reject(
            task.task_id,
            rejected_by="lead@example.com",
            reason="manual inspection first",
        )
    )

    assert rejected.status is TaskStatus.REJECTED
    assert rejected.decision_by == "lead@example.com"
    assert executor.calls == 0


def test_unknown_task_and_invalid_terminal_transition_are_explicit():
    from app.orchestrator import InvalidTransitionError, TaskNotFoundError

    system, _ = make_system()
    with pytest.raises(TaskNotFoundError):
        run(system.approve("missing", approved_by="ops@example.com"))

    task = run(system.submit(IncidentRequest(
        request_id="incident-004",
        asset_id="line-1",
        summary="Known anomaly requiring review",
    )))
    run(system.reject(task.task_id, rejected_by="lead@example.com", reason="defer"))
    with pytest.raises(InvalidTransitionError):
        run(system.approve(task.task_id, approved_by="ops@example.com"))


def test_duplicate_execution_claim_before_completion_is_rejected():
    from app.orchestrator import InvalidTransitionError

    system, _ = make_system()
    task = run(system.submit(IncidentRequest(
        request_id="incident-005",
        asset_id="line-11",
        summary="Intermittent actuator fault",
    )))
    assert run(system.store.claim_execution(task.task_id)) is True
    with pytest.raises(InvalidTransitionError, match="already claimed"):
        run(system.approve(task.task_id, approved_by="ops@example.com"))

class LosingCreateRaceStore(InMemoryTaskStore):
    def __init__(self, existing):
        super().__init__()
        self.existing = existing
        self.lookups = 0

    async def get_by_request_id(self, request_id):
        self.lookups += 1
        if self.lookups == 1:
            return None
        return self.existing

    async def create(self, task):
        return self.existing


class CountingPlanner(Planner):
    def __init__(self):
        self.calls = 0

    async def plan(self, request):
        self.calls += 1
        return await super().plan(request)


def test_submit_losing_creation_race_does_not_repeat_agent_work():
    request = IncidentRequest(
        request_id="incident-race",
        asset_id="line-race",
        summary="Concurrent duplicate request",
    )
    existing = TaskRecord(
        task_id="task-winner",
        request=request,
        status=TaskStatus.INVESTIGATING,
    )
    planner = CountingPlanner()
    store = LosingCreateRaceStore(existing)
    system = Orchestrator(
        store=store,
        planner=planner,
        investigator=Investigator(),
        executor=Executor(),
    )

    returned = run(system.submit(request))

    assert returned.task_id == "task-winner"
    assert planner.calls == 0
