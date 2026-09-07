import asyncio

import pytest

from app.domain import IncidentInput, TaskStatus
from app.orchestrator import IncidentOrchestrator
from app.store import InMemoryTaskStore
from app.tools import ManufacturingTools


@pytest.mark.asyncio
async def test_same_idempotency_key_returns_same_task():
    store = InMemoryTaskStore()
    orchestrator = IncidentOrchestrator(store)
    incident = IncidentInput(line_id="PACK-03", description="Packaging line stopped twice and output is down")

    first = await orchestrator.submit(incident, "incident-123")
    second = await orchestrator.submit(incident, "incident-123")

    assert first.id == second.id
    assert second.status == TaskStatus.WAITING_APPROVAL


@pytest.mark.asyncio
async def test_transient_tool_failures_are_retried():
    tools = ManufacturingTools(failure_budget={"get_line_metrics": 2})
    orchestrator = IncidentOrchestrator(InMemoryTaskStore(), tools)
    incident = IncidentInput(line_id="PACK-03", description="Output dropped after two intermittent stops")

    task = await orchestrator.submit(incident, "retry-demo")

    assert task.status == TaskStatus.WAITING_APPROVAL
    assert tools.failure_budget["get_line_metrics"] == 0


@pytest.mark.asyncio
async def test_duplicate_approval_executes_side_effect_once():
    tools = ManufacturingTools()
    orchestrator = IncidentOrchestrator(InMemoryTaskStore(), tools)
    incident = IncidentInput(line_id="PACK-03", description="Output dropped after two intermittent stops")
    task = await orchestrator.submit(incident, "approval-demo")

    first, second = await asyncio.gather(
        orchestrator.approve(task.id, "Mauricio"),
        orchestrator.approve(task.id, "Mauricio"),
    )

    assert len(tools.created_tickets) == 1
    completed = first if first.status == TaskStatus.COMPLETED else second
    assert completed.status == TaskStatus.COMPLETED
