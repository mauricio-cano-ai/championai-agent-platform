from __future__ import annotations

from hashlib import sha256
from typing import Protocol

from app.agents import ExecutorAgent, InvestigatorAgent, PlannerAgent
from app.domain import IncidentInput, IncidentPlan, TaskStatus, TaskView, TraceEvent
from app.mcp_tools_client import MCPManufacturingClient
from app.reliability import retry_async
from app.store import TaskStore
from app.tools import ManufacturingTools


class PlannerProtocol(Protocol):
    async def plan(self, incident: IncidentInput) -> IncidentPlan:
        ...


class IncidentOrchestrator:
    def __init__(
        self,
        store: TaskStore,
        tools: ManufacturingTools | None = None,
        mcp_client: MCPManufacturingClient | None = None,
        planner: PlannerProtocol | None = None,
    ) -> None:
        self.store = store
        self.tools = tools or ManufacturingTools()

        # Tests keep the deterministic planner by default.
        # Runtime can inject OpenAIPlannerAgent.
        self.planner = planner or PlannerAgent()
        self.executor = ExecutorAgent()

        if mcp_client is not None:
            self.investigator = InvestigatorAgent(
                mcp_client=mcp_client
            )
            self.evidence_transport = "mcp"
        else:
            self.investigator = InvestigatorAgent(
                tools=self.tools
            )
            self.evidence_transport = "direct"

    async def submit(
        self,
        incident: IncidentInput,
        idempotency_key: str,
    ) -> TaskView:
        existing = await self.store.get_by_idempotency_key(
            idempotency_key
        )

        if existing:
            existing.trace.append(
                TraceEvent(
                    kind="idempotency_hit",
                    detail={"key": idempotency_key},
                )
            )
            return existing

        task = TaskView(
            idempotency_key=idempotency_key,
            incident=incident,
        )

        task.trace.append(
            TraceEvent(
                kind="received",
                detail={"line_id": incident.line_id},
            )
        )

        await self.store.save(task)

        task.status = TaskStatus.INVESTIGATING

        task.plan = await self.planner.plan(incident)

        task.trace.append(
            TraceEvent(
                kind="plan_created",
                detail={
                    "steps": len(task.plan.steps),
                    "planner": type(self.planner).__name__,
                },
            )
        )

        await self.store.save(task)

        try:
            task.evidence = await self.investigator.investigate(
                incident
            )

            task.trace.append(
                TraceEvent(
                    kind="tools_completed",
                    detail={
                        "tools": [
                            evidence.tool
                            for evidence in task.evidence
                        ],
                        "transport": self.evidence_transport,
                    },
                )
            )

            task.proposal = await self.executor.propose(
                incident,
                task.evidence,
            )

            task.status = TaskStatus.WAITING_APPROVAL

            task.trace.append(
                TraceEvent(
                    kind="human_approval_required",
                    detail={
                        "action": task.proposal.action_type
                    },
                )
            )

        except Exception as exc:
            task.status = TaskStatus.FAILED

            task.result = {
                "error": type(exc).__name__,
                "message": str(exc),
            }

            task.trace.append(
                TraceEvent(
                    kind="failed",
                    detail=task.result,
                )
            )

        return await self.store.save(task)

    async def approve(
        self,
        task_id: str,
        approved_by: str,
    ) -> TaskView:
        task = await self.store.get(task_id)

        if not task:
            raise KeyError(task_id)

        if task.status == TaskStatus.COMPLETED:
            task.trace.append(
                TraceEvent(
                    kind="duplicate_approval_ignored",
                    detail={"approved_by": approved_by},
                )
            )
            return task

        if (
            task.status != TaskStatus.WAITING_APPROVAL
            or not task.proposal
        ):
            raise ValueError(
                f"Task {task_id} is not awaiting approval"
            )

        action_id = sha256(
            f"{task.id}:{task.proposal.action_type}".encode()
        ).hexdigest()

        first_claim = await self.store.claim_action(action_id)

        if not first_claim:
            refreshed = await self.store.get(task_id)
            return refreshed or task

        ticket = await retry_async(
            lambda: self.tools.create_maintenance_ticket(
                action_id=action_id,
                line_id=task.incident.line_id,
                reason=task.proposal.reason,
            )
        )

        task.result = {
            "approved_by": approved_by,
            "maintenance_ticket": ticket,
        }

        task.status = TaskStatus.COMPLETED

        task.trace.append(
            TraceEvent(
                kind="side_effect_executed",
                detail={
                    "action_id": action_id,
                    "ticket_id": ticket["ticket_id"],
                },
            )
        )

        return await self.store.save(task)
